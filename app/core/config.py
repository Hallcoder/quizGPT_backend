from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "QuizGPT"
    DEBUG: bool = True
    SECRET_KEY: str

    DATABASE_URL: str
    OPENAI_API_KEY: str

    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000"

    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
