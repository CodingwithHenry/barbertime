from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID: str

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@barbertime.app"

    FRONTEND_URL: str = "http://localhost:5173"
    RESERVATION_WINDOW_MINUTES: int = 15
    RATE_LIMIT_RESERVATIONS_PER_DAY: int = 1

    class Config:
        env_file = ".env"


settings = Settings()
