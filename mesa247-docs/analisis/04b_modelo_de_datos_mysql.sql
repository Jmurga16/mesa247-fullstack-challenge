-- =====================================================================
-- Mesa247 · Lista de espera — DDL de referencia (MySQL 8, InnoDB, utf8mb4)
-- Fuera del track: sirve para pensar el modelo. En el repo, las tablas
-- las crea SQLAlchemy/Alembic. Todos los DATETIME están en UTC.
-- En el prototipo de 4 h bastan: locations, host_devices, tickets, ticket_events.
-- Probado el 15/09/2026 en MariaDB 10.11: creación de tablas, turno activo único,
-- UPDATE condicional (1.º llamado = 1 fila, 2.º = 0) y consulta del reporte.
-- OJO: MariaDB no es MySQL. Es evidencia parcial; antes del piloto hay que correrlo contra MySQL 8.
-- =====================================================================

CREATE TABLE locations (
  id                  INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  external_ref        VARCHAR(64)      NULL,                 -- id del local en El Libro
  public_code         VARCHAR(16)      NOT NULL COLLATE utf8mb4_bin,  -- va impreso en el QR: /q/{public_code}
  name                VARCHAR(120)     NOT NULL,
  country_code        CHAR(2)          NOT NULL,             -- PE, CL, EC, CO
  timezone            VARCHAR(64)      NOT NULL,             -- America/Lima, America/Santiago
  day_cutoff_hour     TINYINT UNSIGNED NOT NULL DEFAULT 5,   -- el día de servicio termina a las 05:00 local
  minutes_per_party   TINYINT UNSIGNED NOT NULL DEFAULT 4,   -- respaldo del estimador de espera
  call_grace_minutes  TINYINT UNSIGNED NOT NULL DEFAULT 10,  -- tolerancia después de llamar
  max_party_size      TINYINT UNSIGNED NOT NULL DEFAULT 20,
  is_active           BOOLEAN          NOT NULL DEFAULT TRUE,
  created_at          DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uq_locations_public_code (public_code),
  UNIQUE KEY uq_locations_external_ref (external_ref)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE host_devices (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  location_id   INT UNSIGNED NOT NULL,
  label         VARCHAR(60)  NOT NULL,                       -- "Tablet puerta"
  token_hash    CHAR(64)     NOT NULL COLLATE utf8mb4_bin,   -- sha256 del token; el token nunca se guarda en claro
  created_at    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  last_seen_at  DATETIME(3)  NULL,                           -- alimenta la alarma "tablet desconectada"
  revoked_at    DATETIME(3)  NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_host_devices_token_hash (token_hash),
  KEY ix_host_devices_location (location_id),
  CONSTRAINT fk_host_devices_location FOREIGN KEY (location_id) REFERENCES locations (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tickets (
  id                 BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  public_token       VARCHAR(32)      NOT NULL COLLATE utf8mb4_bin,  -- secrets.token_urlsafe(16) → 22 chars
                                                            -- binaria: es credencial, no texto
  location_id        INT UNSIGNED     NOT NULL,
  service_date       DATE             NOT NULL,              -- día de servicio local
  source             ENUM('qr','host') NOT NULL,
  customer_name      VARCHAR(40)      NOT NULL,
  phone_e164         VARCHAR(16)      NULL,                  -- NULL si el anfitrión lo agregó sin teléfono
  party_size         TINYINT UNSIGNED NOT NULL,
  status             ENUM('waiting','called','seated','cancelled','no_show','removed','expired')
                                      NOT NULL DEFAULT 'waiting',
  sort_key           BIGINT           NOT NULL,              -- ms de llegada. NUNCA se usa solo:
                                                            -- se ordena y cuenta por (sort_key, id)
  quoted_wait_min    SMALLINT UNSIGNED NULL,                 -- lo prometido al unirse (calibración)
  position_at_join   SMALLINT UNSIGNED NULL,
  call_count         TINYINT UNSIGNED NOT NULL DEFAULT 0,
  joined_at          DATETIME(3)      NOT NULL,
  called_at          DATETIME(3)      NULL,
  on_the_way_at      DATETIME(3)      NULL,                  -- «Voy en camino» es una marca, no un estado
  seated_at          DATETIME(3)      NULL,
  closed_at          DATETIME(3)      NULL,                  -- momento del estado final
  consent_at         DATETIME(3)      NULL,
  active_key         VARCHAR(64)      NULL,                  -- "{location_id}:{service_date}:{phone}" mientras está
                                                            -- activo; NULL al cerrar y si no hay teléfono.
                                                            -- Con la fecha: el pendiente de ayer no bloquea hoy.
  client_request_id  CHAR(36)         NULL,                  -- UUID del cliente (tablet Y navegador público)
                                                            -- generado antes de enviar → reintento = mismo turno
  updated_at         DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uq_tickets_public_token (public_token),
  UNIQUE KEY uq_tickets_active_key (active_key),                        -- 1 turno activo por teléfono+local+día
  UNIQUE KEY uq_tickets_client_request (location_id, client_request_id),-- idempotencia del alta
  KEY ix_tickets_queue (location_id, service_date, status, sort_key),  -- la consulta de cada 5–15 s
  KEY ix_tickets_report (location_id, service_date, status),
  CONSTRAINT fk_tickets_location FOREIGN KEY (location_id) REFERENCES locations (id),
  -- Techo absoluto del dato. El límite de negocio es locations.max_party_size (20 por defecto),
  -- que valida Pydantic con la fila del local. Son dos cosas distintas, a propósito.
  CONSTRAINT ck_tickets_party_size CHECK (party_size BETWEEN 1 AND 50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ticket_events (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  ticket_id    BIGINT UNSIGNED NOT NULL,
  location_id  INT UNSIGNED    NOT NULL,
  type         VARCHAR(32)     NOT NULL,   -- joined, called, recalled, call_undone, on_the_way, seated, left,
                                           -- cancelled, no_show, removed, expired, notification_sent,
                                           -- notification_failed, notification_delivered, notification_read
  actor        VARCHAR(40)     NOT NULL,   -- customer | host_device:{id} | system | whatsapp
  data         JSON            NULL,
  created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY ix_ticket_events_ticket (ticket_id, created_at),
  KEY ix_ticket_events_location (location_id, created_at),
  CONSTRAINT fk_ticket_events_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------- Fase 2 -------------------------------

CREATE TABLE notifications (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  ticket_id            BIGINT UNSIGNED NOT NULL,
  location_id          INT UNSIGNED    NOT NULL,
  channel              ENUM('whatsapp','sms','fake') NOT NULL,
  kind                 VARCHAR(32)     NOT NULL,              -- table_ready
  attempt_key          VARCHAR(64)     NOT NULL,              -- "{ticket_id}:{call_count}:{channel}" → idempotencia
  status               ENUM('pending','sent','delivered','read','failed') NOT NULL DEFAULT 'pending',
  provider_message_id  VARCHAR(128)    NULL,                  -- id de Meta (wamid...) para mapear estados
  attempts             TINYINT UNSIGNED NOT NULL DEFAULT 0,
  last_error           VARCHAR(255)    NULL,
  created_at           DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  sent_at              DATETIME(3)     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_notifications_attempt_key (attempt_key),
  UNIQUE KEY uq_notifications_provider_id (provider_message_id),
  KEY ix_notifications_status (status, created_at),
  CONSTRAINT fk_notifications_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE webhook_events (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  provider     VARCHAR(16)     NOT NULL,                      -- whatsapp
  external_id  VARCHAR(128)    NOT NULL,                      -- id del mensaje o estado recibido
  payload      JSON            NOT NULL,
  received_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uq_webhook_events_external (provider, external_id)   -- Meta reintenta: procesar una sola vez
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE daily_reports (
  location_id         INT UNSIGNED      NOT NULL,
  service_date        DATE              NOT NULL,
  joined              SMALLINT UNSIGNED NOT NULL,
  seated              SMALLINT UNSIGNED NOT NULL,
  left_without_seat   SMALLINT UNSIGNED NOT NULL,
  no_show_after_call  SMALLINT UNSIGNED NOT NULL,
  avg_wait_min        SMALLINT UNSIGNED NULL,
  generated_at        DATETIME(3)       NOT NULL,
  emailed_at          DATETIME(3)       NULL,                  -- el correo sale una sola vez
  PRIMARY KEY (location_id, service_date),
  CONSTRAINT fk_daily_reports_location FOREIGN KEY (location_id) REFERENCES locations (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------- Consultas de referencia -----------------------

-- Cola del anfitrión (cada 5 s). El filtro por service_date NO es opcional:
-- sin él, un turno que quedó abierto ayer sigue apareciendo hoy.
-- SELECT id, customer_name, party_size, status, joined_at, called_at, on_the_way_at
--   FROM tickets
--  WHERE location_id = ? AND service_date = ? AND status IN ('waiting','called')
--  ORDER BY sort_key, id;

-- Grupos delante del comensal (desempate por id: dos altas pueden caer en el mismo ms)
-- SELECT COUNT(*) FROM tickets
--  WHERE location_id = ? AND service_date = ? AND status = 'waiting'
--    AND (sort_key < ? OR (sort_key = ? AND id < ?));

-- Reporte del día (con el día ya cerrado)
-- SELECT COUNT(*) AS se_unieron,
--        SUM(status = 'seated') AS se_sentaron,
--        SUM(status = 'expired' OR (status = 'cancelled' AND called_at IS NULL)) AS se_fueron_sin_sentarse,
--        SUM(status = 'no_show' OR (status = 'cancelled' AND called_at IS NOT NULL)) AS no_vinieron_al_ser_llamados,
--        ROUND(AVG(CASE WHEN status = 'seated' THEN TIMESTAMPDIFF(SECOND, joined_at, seated_at) END) / 60) AS espera_media_min
--   FROM tickets
--  WHERE location_id = ? AND service_date = ? AND status <> 'removed';
-- Ojo: sin filas, COUNT da 0 pero SUM y AVG dan NULL. "Sin datos" y "cero" se muestran distinto.
-- Ojo 2: TIMESTAMPDIFF no existe en SQLite. En el código, el promedio se calcula en Python.
