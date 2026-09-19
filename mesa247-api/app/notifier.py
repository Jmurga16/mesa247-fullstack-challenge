import logging
from typing import Protocol

from app.domain.queue import add_event

logger = logging.getLogger("mesa247.notifier")


class Notifier(Protocol):
    def send_table_ready(self, ticket) -> None:
        """Envía el aviso o lanza una excepción. No decide el estado del turno."""


def masked(phone):
    return f"***{phone[-3:]}" if phone else "sin teléfono"


class FakeNotifier:
    # El corte no envía WhatsApp real: registra el aviso con el teléfono enmascarado.
    def send_table_ready(self, ticket) -> None:
        logger.info("WhatsApp simulado | turno %s | %s: tu mesa está lista.",
                    ticket.id, masked(ticket.phone_e164))


_notifier = FakeNotifier()


def get_notifier() -> Notifier:
    return _notifier


def notify_called(session, ticket, notifier: Notifier, instant):
    # Fuera de la transición del llamado y en su propia transacción: si el proveedor
    # falla, el turno sigue llamado y solo queda el evento notification_failed.
    try:
        notifier.send_table_ready(ticket)
        kind, data = "notification_sent", {"channel": "whatsapp_fake"}
    except Exception as error:
        logger.warning("Aviso no entregado para el turno %s", ticket.id)
        kind, data = "notification_failed", {"channel": "whatsapp_fake", "reason": type(error).__name__}
    try:
        add_event(session, ticket, kind, "system", instant, data)
        session.commit()
    except Exception:
        session.rollback()
        logger.error("No se pudo registrar el aviso del turno %s", ticket.id)
