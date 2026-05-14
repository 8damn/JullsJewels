from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    app_env: str = "development"
    database_url: str = "sqlite:///./jullsjewels.db"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    max_upload_size_mb: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
