from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    app_env: str = "development"
    database_url: str = "sqlite:///./jullsjewels.db"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080      # legacy — zachováno pro confirmation tokeny
    jwt_access_expire_minutes: int = 60  # access token: 1 hodina
    jwt_refresh_expire_days: int = 7     # refresh token: 7 dní
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    max_upload_size_mb: int = 5

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        """SECRET_KEY musí být >= 32 znaků a nemůže být default placeholder.
        Tímto klíčem se podepisuje JWT i session cookie — únik = kompromitace."""
        if not v:
            raise ValueError("SECRET_KEY nesmí být prázdný")
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY musí mít alespoň 32 znaků (má {len(v)}). "
                "Vygeneruj: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if v.startswith("change-this") or v == "secret" or v == "changeme":
            raise ValueError(
                "SECRET_KEY je nastaven na default/placeholder. "
                "Vygeneruj reálný klíč: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    class Config:
        env_file = ".env"


settings = Settings()
