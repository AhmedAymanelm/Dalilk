from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    API_KEY: str
    FILE_TYPE: List
    MAX_FILE_SIZE: int
    FILE_CHUNK_SIZE: int

    DATABASE_URL: str
    DATABASE_NAME: str

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    # Backwards-compatible default settings for providers (new names)
    OPENAI_DEFAULT_TEMPERATURE: Optional[float] = None
    OPENAI_DEFAULT_INPUT_MAX_CHARACTER: Optional[int] = None
    OPENAI_DEFAULT_OUTPUT_MAX_CHARACTER: Optional[int] = None

    COHERE_DEFAULT_TEMPERATURE: Optional[float] = None
    COHERE_DEFAULT_INPUT_MAX_CHARACTER: Optional[int] = None
    COHERE_DEFAULT_OUTPUT_MAX_CHARACTER: Optional[int] = None

    GENERATION_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_SIZE: Optional[int] = None
    INPUT_DAFAULT_MAX_CHARACTERS: Optional[int] = None
    GENERATION_DAFAULT_MAX_TOKENS: Optional[int] = None
    GENERATION_DAFAULT_TEMPERATURE: Optional[float] = None

    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DESTANCE: Optional[str] = None

    class Config:
        env_file = ".env"


def get_settings():
    s = Settings()

    # Backfill provider-specific defaults from legacy/misspelled fields
    try:
        # Temperature fallbacks
        if getattr(s, "OPENAI_DEFAULT_TEMPERATURE", None) is None:
            s.OPENAI_DEFAULT_TEMPERATURE = getattr(s, "GENERATION_DAFAULT_TEMPERATURE", None)
        if getattr(s, "COHERE_DEFAULT_TEMPERATURE", None) is None:
            s.COHERE_DEFAULT_TEMPERATURE = getattr(s, "GENERATION_DAFAULT_TEMPERATURE", None)

        # Input max characters fallback
        if getattr(s, "OPENAI_DEFAULT_INPUT_MAX_CHARACTER", None) is None:
            s.OPENAI_DEFAULT_INPUT_MAX_CHARACTER = getattr(s, "INPUT_DAFAULT_MAX_CHARACTERS", None)
        if getattr(s, "COHERE_DEFAULT_INPUT_MAX_CHARACTER", None) is None:
            s.COHERE_DEFAULT_INPUT_MAX_CHARACTER = getattr(s, "INPUT_DAFAULT_MAX_CHARACTERS", None)

        # Output max character / max tokens fallback
        if getattr(s, "OPENAI_DEFAULT_OUTPUT_MAX_CHARACTER", None) is None:
            s.OPENAI_DEFAULT_OUTPUT_MAX_CHARACTER = getattr(s, "GENERATION_DAFAULT_MAX_TOKENS", None)
        if getattr(s, "COHERE_DEFAULT_OUTPUT_MAX_CHARACTER", None) is None:
            s.COHERE_DEFAULT_OUTPUT_MAX_CHARACTER = getattr(s, "GENERATION_DAFAULT_MAX_TOKENS", None)
    except Exception:
        # be permissive; if any attribute is missing just continue
        pass

    return s