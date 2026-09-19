"""Functional browser checks against real Vite/FastAPI and disposable SQLite.

Run with the API virtualenv after installing tests/requirements.txt and Chromium.
The runner never uses the database or servers from the developer's session.
"""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "mesa247-api"
WEB = ROOT / "mesa247-web"
OUT = ROOT / ".artifacts" / "functional"
CODE = "terraza-lima"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def ready(url, process):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server exited with {process.returncode}; see {OUT}")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not start: {url}")


class Stack:
    def __init__(self, folder):
        self.db = Path(folder) / "functional.db"
        self.api_port = free_port()
        self.web_port = free_port()
        self.url = f"http://127.0.0.1:{self.web_port}"
        self.env = dict(os.environ, DATABASE_URL=f"sqlite:///{self.db.as_posix()}",
                        DEMO_MODE="true", CREATE_TABLES="true",
                        DATABASE_SSL_CA="", WEB_BASE_URL=self.url,
                        API_PROXY_TARGET=f"http://127.0.0.1:{self.api_port}")
        self.api_process = self.web_process = None
        self.logs = []

    def launch(self, command, cwd, log_name):
        log = (OUT / log_name).open("a", encoding="utf-8")
        self.logs.append(log)
        return subprocess.Popen(command, cwd=cwd, env=self.env, stdout=log,
                                stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def start_api(self):
        self.api_process = self.launch(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", str(self.api_port), "--no-access-log"], API, "api.log")
        ready(f"http://127.0.0.1:{self.api_port}/readyz", self.api_process)

    def stop_api(self):
        self.stop_process(self.api_process)

    @staticmethod
    def stop_process(process):
        if process and process.poll() is None:
            if os.name == "nt":
                # A Windows virtualenv executable can launch a child interpreter.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, check=True)
            else:
                process.terminate()
            process.wait(timeout=15)

    def start(self):
        seeded = subprocess.run([sys.executable, "seed.py"], cwd=API, env=self.env,
                                capture_output=True, check=True)
        assert len(re.findall(b"Bearer:", seeded.stdout)) == 3
        self.start_api()
        self.web_process = self.launch(
            [shutil.which("node"), str(WEB / "node_modules/vite/bin/vite.js"),
             "--host", "127.0.0.1", "--port", str(self.web_port), "--strictPort"],
            WEB, "vite.log")
        ready(self.url, self.web_process)

    def close(self):
        self.stop_api()
        self.stop_process(self.web_process)
        for log in self.logs:
            log.close()


class Checks:
    def __init__(self, browser, stack):
        self.browser, self.stack = browser, stack
        self.contexts, self.pages, self.errors = [], [], []
        self.counter = 0

    def page(self, mobile=True):
        context = self.browser.new_context(
            viewport={"width": 390, "height": 844} if mobile else {"width": 1024, "height": 768},
            is_mobile=mobile, has_touch=True, locale="es-PE", timezone_id="America/Lima")
        page = context.new_page()
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.contexts.append(context)
        self.pages.append(page)
        return page

    def phone(self):
        self.counter += 1
        return f"+51987{self.counter:06d}"

    def goto(self, page, path):
        page.goto(self.stack.url + path)

    def form(self, page, name, phone, code=CODE):
        self.goto(page, f"/q/{code}")
        page.get_by_label("Nombre", exact=True).fill(name)
        page.get_by_label("Teléfono", exact=True).fill(phone)

    def submit(self, page):
        page.get_by_role("button", name="Unirme a la cola", exact=True).click()

    def join(self, page, name, phone=None, code=CODE):
        self.form(page, name, phone or self.phone(), code)
        self.submit(page)
        page.wait_for_url("**/t/*")
        expect(page.locator(".eta")).to_be_visible()
        return page.url.rsplit("/", 1)[1]

    def host(self, page, code=CODE):
        self.goto(page, "/admin")
        names = {CODE: "La Terraza Azul", "vientos-lima": "Cuatro Vientos",
                 "casa-santiago": "Casa Mediterránea"}
        page.locator(".demo-list li").filter(has_text=names[code]).get_by_role(
            "button", name="Abrir su tablet").click()
        page.wait_for_url("**/host")
        expect(page.locator("h1")).to_contain_text(names[code])
        return page.evaluate("localStorage.getItem('mesa247:host-token')")

    def row(self, page, name):
        return page.locator(".queue-row").filter(has=page.locator(".queue-name", has_text=name))

    def api(self, page, path, method="GET", body=None, token=None):
        response = page.request.fetch(self.stack.url + path, method=method, data=body,
                                      headers={"Authorization": f"Bearer {token}"} if token else {})
        return response.status, response.json()

    def ticket(self, page, token):
        status, ticket = self.api(page, f"/api/public/tickets/{token}")
        assert status == 200
        return ticket

    def sql(self, statement, parameters=()):
        connection = sqlite3.connect(self.stack.db)
        try:
            with connection:
                return connection.execute(statement, parameters).fetchall()
        finally:
            # The connection context manager commits; it does not close its file.
            connection.close()

    def no_overflow(self, page):
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Horizontal overflow"

    def test_01_join_call_seat_polling(self):
        guest, host = self.page(), self.page(False)
        self.goto(guest, "/")
        expect(guest.locator("#demo-location option")).to_have_count(3)
        guest.get_by_label("Local", exact=True).select_option(CODE)
        guest.get_by_role("button", name="Unirme a la lista", exact=True).click()
        expect(guest.get_by_label("Nombre", exact=True)).to_be_visible()
        self.host(host)
        token = self.join(guest, "QA Happy")
        assert self.ticket(guest, token)["groups_ahead"] == 0
        self.no_overflow(guest)
        expect(self.row(host, "QA Happy")).to_be_visible(timeout=8000)
        self.row(host, "QA Happy").get_by_role("button", name="Llamar", exact=True).click()
        expect(guest.locator(".banner-ready")).to_contain_text("tu mesa está lista", timeout=18000)
        expect(guest.locator(".deadline")).to_contain_text("Tienes hasta")
        expect(self.row(host, "QA Happy")).to_contain_text("Aviso enviado")
        self.no_overflow(host)
        guest.screenshot(path=str(OUT / "mobile-called.png"), full_page=True)
        host.screenshot(path=str(OUT / "tablet-called.png"), full_page=True)
        self.row(host, "QA Happy").get_by_role("button", name="Sentar", exact=True).click()
        expect(guest.locator(".closed")).to_be_visible(timeout=18000)
        assert self.ticket(guest, token)["status"] == "seated"
        requests = []
        guest.on("request", lambda request: requests.append(request.url) if "/api/public/tickets/" in request.url else None)
        guest.wait_for_timeout(16000)
        assert not requests, "Terminal ticket keeps polling"

    def test_02_distinct_joins_same_browser(self):
        page = self.page()
        first = self.join(page, "QA First")
        second = self.join(page, "QA Second")
        assert first != second, "Two customers received the same ticket"
        assert self.ticket(page, second)["name"] == "QA Second"
        expect(page.locator(".turn-label")).to_contain_text("1 grupo")

    def test_03_duplicate_and_recovery(self):
        original, other = self.page(), self.page()
        phone = self.phone()
        token = self.join(original, "QA Duplicate", phone)
        self.form(other, "QA Duplicate", phone)
        with other.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/tickets")) as response:
            self.submit(other)
        assert response.value.status == 409
        assert "token" not in response.value.json()
        expect(other.get_by_role("heading", name="Ya estás en la lista", exact=True)).to_be_visible()
        other.get_by_role("button", name="Ver mi turno", exact=True).click()
        other.wait_for_url(f"**/t/{token}")
        self.goto(other, f"/q/{CODE}/mi-turno")
        other.get_by_label("Teléfono con el que te anotaste").fill(phone)
        other.get_by_role("button", name="Ver mi turno").click()
        other.wait_for_url(f"**/t/{token}")

    def test_04_validation_and_party_limits(self):
        page = self.page()
        self.form(page, "", "+51987123456")
        self.submit(page)
        expect(page.get_by_role("alert")).to_contain_text("nombre")
        page.get_by_label("Nombre", exact=True).fill("QA Validation")
        page.get_by_label("Teléfono", exact=True).fill("123")
        self.submit(page)
        expect(page.get_by_role("alert")).to_contain_text("código de país")
        page.get_by_role("button", name="Quitar una persona").click()
        expect(page.get_by_role("button", name="Quitar una persona")).to_be_disabled()
        for _ in range(19):
            page.get_by_role("button", name="Agregar una persona").click()
        expect(page.locator("output")).to_have_text("20")
        expect(page.get_by_role("button", name="Agregar una persona")).to_be_disabled()

    def test_05_chile_and_foreign_phone(self):
        page = self.page()
        self.goto(page, "/q/casa-santiago")
        expect(page.get_by_label("Teléfono", exact=True)).to_have_value("+56 ")
        token = self.join(page, "QA Chile", "+56987654321", "casa-santiago")
        assert self.ticket(page, token)["location_name"] == "Casa Mediterránea"
        token = self.join(page, "QA Foreign", "+34612345678")
        assert self.ticket(page, token)["status"] == "waiting"

    def test_06_cancel_rejoin_and_lookup_absence(self):
        page = self.page()
        phone = self.phone()
        token = self.join(page, "QA Cancel", phone)
        page.get_by_role("button", name="Ya no voy", exact=True).click()
        page.get_by_role("button", name="Sigo esperando").click()
        assert self.ticket(page, token)["status"] == "waiting"
        page.get_by_role("button", name="Ya no voy", exact=True).click()
        page.get_by_role("button", name="Sí, ya no voy").click()
        expect(page.locator(".closed")).to_be_visible()
        assert self.ticket(page, token)["status"] == "cancelled"
        self.goto(page, f"/q/{CODE}/mi-turno")
        page.get_by_label("Teléfono con el que te anotaste").fill(phone)
        page.get_by_role("button", name="Ver mi turno").click()
        expect(page.get_by_role("alert")).to_contain_text("No encontramos una espera activa")
        assert self.join(page, "QA Rejoined", phone) != token

    def test_07_restart_loses_position(self):
        page = self.page()
        phone = self.phone()
        token = self.join(page, "QA Restart", phone)
        self.join(page, "QA Ahead")
        self.form(page, "QA Restart", phone)
        self.submit(page)
        page.get_by_role("button", name="Registrarme de nuevo").click()
        expect(page.locator(".confirm")).to_contain_text("al final de la cola")
        page.get_by_role("button", name="Sí, empezar de nuevo").click()
        page.wait_for_url("**/t/*")
        assert page.url.rsplit("/", 1)[1] != token
        assert self.ticket(page, token)["status"] == "cancelled"

    def test_08_host_actions_and_report(self):
        guest, host = self.page(), self.page(False)
        bearer = self.host(host)
        for suffix, action, expected in [("Leave", "Se fue", "cancelled"),
                                         ("NoShow", "No vino", "no_show"),
                                         ("Remove", "Borrar", "removed")]:
            name = "QA " + suffix
            token = self.join(guest, name)
            host.get_by_role("button", name="Actualizar", exact=True).click()
            row = self.row(host, name)
            expect(row).to_be_visible()
            if action == "No vino":
                row.get_by_role("button", name="Llamar", exact=True).click()
            row.get_by_role("button", name=action, exact=True).click()
            if action == "Borrar":
                row.get_by_role("button", name="Confirmar", exact=True).click()
            expect(row).to_have_count(0)
            assert self.ticket(guest, token)["status"] == expected
        host.get_by_role("link", name="Reporte del día").click()
        expect(host.locator(".report-lines")).to_be_visible()
        _, report = self.api(host, "/api/host/report", token=bearer)
        assert report["joined"] == sum(report[k] for k in ("seated", "left_before_seating", "no_show", "pending"))
        for label, key in [("Se unieron", "joined"), ("Se sentaron", "seated"),
                           ("Se fueron sin sentarse", "left_before_seating"),
                           ("No vinieron al ser llamados", "no_show")]:
            expect(host.locator(".report-line").filter(has=host.locator("dt", has_text=re.compile("^" + label + "$"))).locator("dd")).to_have_text(str(report[key]))
        expect(host.get_by_role("status")).to_contain_text("sin desenlace")
        self.no_overflow(host)
        host.screenshot(path=str(OUT / "report.png"), full_page=True)
        host.get_by_label("Día de servicio").fill("2020-01-01")
        expect(host.locator(".report-line").first.locator("dd")).to_have_text("0")
        host.get_by_role("button", name="Volver a hoy").click()
        expect(host.locator(".report-line").first.locator("dd")).to_have_text(str(report["joined"]))

    def test_09_isolation_and_invalid_tokens(self):
        guest, host = self.page(), self.page(False)
        ticket_token = self.join(guest, "QA Isolated")
        bearer = self.host(host, "vientos-lima")
        expect(self.row(host, "QA Isolated")).to_have_count(0)
        ticket_id = self.sql("SELECT id FROM tickets WHERE public_token=?", (ticket_token,))[0][0]
        status, _ = self.api(host, f"/api/host/tickets/{ticket_id}/call", "POST", token=bearer)
        assert status == 404
        self.goto(host, "/host?token=invalid-functional-token")
        expect(host.get_by_role("heading", name="Esta tablet no tiene sesión")).to_be_visible()
        assert "token=" not in host.url
        self.goto(guest, "/t/invalid-functional-token")
        expect(guest.get_by_role("heading", name="No encontramos este turno")).to_be_visible()
        self.goto(guest, "/q/invalid-local")
        expect(guest.get_by_role("heading", name="No encontramos este local")).to_be_visible()

    def test_10_retry_after_lost_response(self):
        page = self.page()
        self.form(page, "QA Retry", self.phone())
        request_ids = []

        def lose_once(route):
            request_ids.append(route.request.post_data_json["request_id"])
            response = route.fetch()
            assert response.status in (200, 201)
            if len(request_ids) == 1:
                route.abort("failed")
            else:
                route.fulfill(response=response)

        page.route("**/api/public/locations/*/tickets", lose_once)
        self.submit(page)
        expect(page.get_by_role("alert")).to_contain_text("Sin conexión")
        self.submit(page)
        page.wait_for_url("**/t/*")
        assert len(request_ids) == 2 and request_ids[0] == request_ids[1]
        assert self.sql("SELECT count(*) FROM tickets WHERE customer_name='QA Retry'")[0][0] == 1

    def test_11_retry_after_reload(self):
        page = self.page()
        phone, ids = self.phone(), []
        self.form(page, "QA Reload", phone)

        def lose_once(route):
            ids.append(route.request.post_data_json["request_id"])
            response = route.fetch()
            if len(ids) == 1:
                route.abort("failed")
            else:
                route.fulfill(response=response)

        page.route("**/api/public/locations/*/tickets", lose_once)
        self.submit(page)
        expect(page.get_by_role("alert")).to_contain_text("Sin conexión")
        page.reload()
        page.get_by_label("Nombre", exact=True).fill("QA Reload")
        page.get_by_label("Teléfono", exact=True).fill(phone)
        self.submit(page)
        page.wait_for_timeout(500)
        assert len(ids) == 2 and ids[0] == ids[1], "Reload loses request_id; resend returns 409 instead of recovering the same ticket"
        page.wait_for_url("**/t/*")

    def test_12_report_session_revoked(self):
        host = self.page(False)
        self.host(host)
        host.get_by_role("link", name="Reporte del día").click()
        expect(host.locator(".report-lines")).to_be_visible()
        self.api(host, f"/api/demo/locations/{CODE}/tablet", "POST")
        host.get_by_role("button", name="Actualizar", exact=True).click()
        host.wait_for_timeout(500)
        assert not self.errors, "Report crashes when its session is revoked: " + "; ".join(self.errors)
        expect(host.get_by_role("heading", name="Esta tablet no tiene sesión")).to_be_visible()

    def test_13_countdown_without_new_responses(self):
        guest, host = self.page(), self.page(False)
        token = self.join(guest, "QA Countdown")
        self.host(host)
        self.row(host, "QA Countdown").get_by_role("button", name="Llamar", exact=True).click()
        expect(guest.locator(".deadline")).to_contain_text("Quedan 10 min", timeout=18000)
        # Advance the browser's timers, not business timestamps or API responses.
        guest.clock.install()
        guest.context.set_offline(True)
        guest.clock.fast_forward(61000)
        expect(guest.locator(".deadline")).to_contain_text("Quedan 9 min", timeout=2000)
        assert self.ticket(host, token)["status"] == "called"

    def test_14_browser_network_recovery(self):
        guest = self.page()
        self.join(guest, "QA Network")
        before = guest.locator(".turn").inner_text()
        guest.context.set_offline(True)
        expect(guest.get_by_role("status")).to_contain_text("Sin conexión", timeout=18000)
        assert guest.locator(".turn").inner_text() == before
        guest.context.set_offline(False)
        expect(guest.get_by_text("Sin conexión", exact=False)).to_have_count(0, timeout=5000)
        expect(guest.locator(".eta")).to_be_visible()

    def test_15_backend_outage_30_seconds(self):
        guest, host = self.page(), self.page(False)
        self.join(guest, "QA Outage")
        self.host(host)
        previous = guest.locator(".turn").inner_text()
        successful_polls = []
        guest.on("response", lambda response: successful_polls.append(response.status)
                 if "/api/public/tickets/" in response.url and response.status == 200 else None)
        self.stack.stop_api()
        started = time.monotonic()
        try:
            guest.wait_for_timeout(30500)
            outage_seconds = time.monotonic() - started
            assert guest.locator(".turn").inner_text() == previous
            offline = guest.get_by_text("Sin conexión", exact=False).count() > 0
            polls_before_restart = len(successful_polls)
        finally:
            self.stack.start_api()
        # Give even the maximum documented 60-second backoff time to recover.
        guest.wait_for_timeout(65000)
        recovered = len(successful_polls) > polls_before_restart
        assert offline and recovered, (
            f"Backend stopped for {outage_seconds:.0f}s; observed 65s after restart: "
            f"offline banner={offline}, automatic recovery={recovered}; "
            "Vite 500 is treated as a permanent API error")

    def test_16_initial_ticket_network_failure(self):
        guest = self.page()
        token = self.join(guest, "QA Initial Offline")
        guest.route("**/api/public/tickets/*", lambda route: route.abort("failed"))
        self.goto(guest, f"/t/{token}")
        guest.wait_for_timeout(500)
        expect(guest.get_by_text("Sin conexión", exact=False)).to_be_visible(timeout=2000)

    def test_17_double_call_two_tablets(self):
        guest, host = self.page(), self.page(False)
        token = self.join(guest, "QA DoubleCall")
        bearer = self.host(host)
        second = self.page(False)
        self.goto(second, f"/host?token={bearer}")
        expect(self.row(second, "QA DoubleCall")).to_be_visible()
        # Hold the second tablet's next poll so both buttons retain the observed waiting row.
        second.route("**/api/host/queue", lambda route: route.abort("failed"))
        self.row(host, "QA DoubleCall").get_by_role("button", name="Llamar", exact=True).click()
        self.row(second, "QA DoubleCall").get_by_role("button", name="Llamar", exact=True).click()
        expect(self.row(host, "QA DoubleCall")).to_contain_text("Aviso enviado")
        events = dict(self.sql("SELECT e.type, count(*) FROM ticket_events e JOIN tickets t ON t.id=e.ticket_id WHERE t.public_token=? GROUP BY e.type", (token,)))
        assert events.get("called") == 1 and events.get("notification_sent") == 1, events

    def cleanup(self):
        for context in self.contexts:
            context.close()
        self.contexts, self.pages, self.errors = [], [], []


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="mesa247-functional-") as folder:
        stack = Stack(folder)
        try:
            stack.start()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                checks = Checks(browser, stack)
                for name in sorted(name for name in dir(checks) if name.startswith("test_")):
                    started = time.monotonic()
                    result = {"name": name, "status": "passed"}
                    try:
                        getattr(checks, name)()
                        assert not checks.errors, "Browser errors: " + "; ".join(checks.errors)
                    except Exception as error:
                        result.update(status="failed", error=str(error))
                        for index, page in enumerate(checks.pages):
                            try:
                                page.screenshot(path=str(OUT / f"{name}-{index}.png"), full_page=True)
                            except Exception:
                                pass
                    finally:
                        checks.cleanup()
                    result["seconds"] = round(time.monotonic() - started, 2)
                    results.append(result)
                    (OUT / "results.json").write_text(
                        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
                    print(f"{result['status'].upper()} {name} ({result['seconds']}s)", flush=True)
                    if "error" in result:
                        print(result["error"][:1200], flush=True)
                browser.close()
        finally:
            stack.close()
    (OUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    failed = sum(result["status"] == "failed" for result in results)
    print(f"\n{len(results) - failed} passed, {failed} failed. Artifacts: {OUT}")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
