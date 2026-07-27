from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
    GMAIL_LOGIN: str
    GMAIL_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: int
    # def get_db_url(self):
    #     return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
    #             f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # def get_redis_url(self):
    #     return f'redis://{self.REDIS_URL}/0'

class GlobalSettings(BaseSettings):
    KAFKA_URL: str
    APPLICATION_URL: str
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

global_settings = GlobalSettings()

settings = Settings()