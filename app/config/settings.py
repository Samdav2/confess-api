from typing import List
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "CONFESS BACKEND"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "RS256"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://confess.com.ng",
        "https://www.confess.com.ng",
        "https://confess-git-development-feranmibas-projects.vercel.app"

    ]

    ALLOWED_HOSTS: List[str] = ["*"]

    @property
    def JWT_PRIVATE_KEY(self) -> str:
        key = os.getenv("JWT_PRIVATE_KEY")
        if key:
            return key.replace("\\n", "\n")
        try:
            with open("certs/private.pem", "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    @property
    def JWT_PUBLIC_KEY(self) -> str:
        key = os.getenv("JWT_PUBLIC_KEY")
        if key:
            return key.replace("\\n", "\n")
        try:
            with open("certs/public.pem", "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_SSL: bool = True
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_FROM_NAME: str = "CONFESS"

    # Mailjet Settings
    MAILJET_API_KEY: str = os.getenv("MAILJET_API_KEY", "")
    MAILJET_SECRET_KEY: str = os.getenv("MAILJET_SECRET_KEY", "")
    MAILJET_SENDER_NAME: str = "Confess Team"



    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Fix DATABASE_URL for Render (postgres:// -> postgresql+asyncpg://)
# This must be done AFTER loading from env, because BaseSettings overwrites defaults with env vars.
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql://") and "asyncpg" not in settings.DATABASE_URL:
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"DEBUG: Final settings.DATABASE_URL: {settings.DATABASE_URL}")
