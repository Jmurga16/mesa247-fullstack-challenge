from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mesa247 API"
    database_url: str = "sqlite:///./mesa247.db"
    database_ssl_ca: str | None = None
    create_tables: bool = True
    web_base_url: str = "http://localhost:5173"
    # Andamiaje de la demo: abre la tablet de un local con un clic, sin repartir
    # tokens a quien prueba la aplicación. `DEMO_MODE=false` lo apaga entero.
    demo_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
