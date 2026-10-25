import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "APAAR GUARDIAN"
    PROJECT_SUBTITLE: str = "Student Data Integrity & Verification Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "apaar-guardian-demo-secret-key-32-chars-long!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for demo ease
    
    # Database Configuration (SQLite default with PostgreSQL support)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./apaar_guardian.db")
    
    # Demo and Security Settings
    DEMO_MODE: bool = True
    DEMO_OTP: str = os.getenv("DEMO_OTP", "123456")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    
    # Cryptographic Digital Signature Secret / Key (HMAC-SHA256 / Ed25519 seed)
    SIGNING_SECRET: str = os.getenv("SIGNING_SECRET", "apaar-guardian-cryptographic-signing-master-seed-2026")
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
