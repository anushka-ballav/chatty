from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL_SYNC: str 
    DATABASE_URL_ASYNC: str 
    ACCESS_TOKEN: str
    AD_ACCOUNT_ID: str
    API_VERSION: str = "v20.0"
    LOG_LEVEL: str = "INFO"
    GOOGLE_API_KEY: str  # ✨ NEW: Add Google API Key setting

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()