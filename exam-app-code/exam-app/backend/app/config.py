from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://examuser:exampass@db:3306/examdb"
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240
    ADMIN_EMAIL: str = "admin@exam.com"
    ADMIN_PASSWORD: str = "Admin@12345"
    QUESTION_TIME_SECONDS: int = 120
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080"
    SEED_DEMO_EXAM: bool = True

    # --- email ---
    # Off by default so the app runs with no mail server configured.
    MAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_STARTTLS: bool = True
    # Gmail rewrites the sender to the authenticated account, so keep this equal
    # to SMTP_USER unless you're on a provider with a verified domain.
    MAIL_FROM: str = ""
    PORTAL_URL: str = "http://localhost:8080"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
