import json
import os
import logging
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_fallback_private_key = None
_fallback_public_key = None

def _get_fallback_keys():
    global _fallback_private_key, _fallback_public_key
    if not _fallback_private_key or not _fallback_public_key:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            _fallback_private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            _fallback_public_key = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating fallback RSA key pair: {e}")
            _fallback_private_key, _fallback_public_key = "", ""
    return _fallback_private_key, _fallback_public_key


class Settings(BaseSettings):

    PROJECT_NAME: str = "CONFESS BACKEND"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./confess.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-confess-secret-key-change-in-production")
    ALGORITHM: str = "RS256"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://confess.com.ng")

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://confess.com.ng",
        "https://www.confess.com.ng",
        "https://confess-git-development-feranmibas-projects.vercel.app"
    ]

    ALLOWED_HOSTS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        return v

    @property
    def JWT_PRIVATE_KEY(self) -> str:
        key = os.getenv("JWT_PRIVATE_KEY")
        if key:
            return key.replace("\\n", "\n")
        try:
            with open("certs/private.pem", "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("⚠️ JWT_PRIVATE_KEY environment variable not set and certs/private.pem not found. Using auto-generated fallback RSA key.")
            priv, _ = _get_fallback_keys()
            return priv

    @property
    def JWT_PUBLIC_KEY(self) -> str:
        key = os.getenv("JWT_PUBLIC_KEY")
        if key:
            return key.replace("\\n", "\n")
        try:
            with open("certs/public.pem", "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("⚠️ JWT_PUBLIC_KEY environment variable not set and certs/public.pem not found. Using auto-generated fallback RSA key.")
            _, pub = _get_fallback_keys()
            return pub


    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2880

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

    # MTN SMS Settings
    MTN_CLIENT_ID: str = os.getenv("MTN_CLIENT_ID", "")
    MTN_CLIENT_SECRET: str = os.getenv("MTN_CLIENT_SECRET", "")
    MTN_API_BASE_URL: str = os.getenv("MTN_API_BASE_URL", "https://api.mtn.com")
    MTN_SENDER_ID: str = os.getenv("MTN_SENDER_ID", "CONFESS")

    # Kudi SMS Settings
    KUDI_API_KEY: str = os.getenv("KUDI_API_KEY", "")
    KUDI_SENDER_ID: str = os.getenv("KUDI_SENDER_ID", "CONFESS")

    # Paystack Settings
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Fix DATABASE_URL for Railway/Render PostgreSQL (postgres:// or postgresql:// -> postgresql+asyncpg://)
if settings.DATABASE_URL:
    if settings.DATABASE_URL.startswith("postgres://"):
        settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif settings.DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in settings.DATABASE_URL:
        settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"DEBUG: Final settings.DATABASE_URL: {settings.DATABASE_URL}")

