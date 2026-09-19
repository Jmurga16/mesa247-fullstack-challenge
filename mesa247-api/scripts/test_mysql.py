"""Run tests against a unique disposable database in the local Compose server."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def main():
    database = "mesa247_test_" + uuid4().hex
    # Only the local Compose instance; never uses the application's DATABASE_URL.
    url = URL.create("mysql+pymysql", username="root",
                     password=os.environ.get("MYSQL_ROOT_PASSWORD", "root-local-only"),
                     host="127.0.0.1", port=int(os.environ.get("MYSQL_PORT", "3307")))
    engine = create_engine(url, hide_parameters=True)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4"))
    try:
        env = dict(os.environ, MESA247_TEST_DATABASE_URL=url.set(database=database).render_as_string(hide_password=False))
        return subprocess.call([sys.executable, "-m", "pytest", "-q", *sys.argv[1:]], cwd=API_ROOT, env=env)
    finally:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE `{database}`"))
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
