from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    APP_NAME: str
    # CORS_ORIGINS: list
    STATIC_DIR: str
    IMAGE_DIR: str
    REDIS_PASSWORD:str
    REDIS_USER:str
    REDIS_USER_PASSWORD:str

    # @property
    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()