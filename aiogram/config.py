from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
    BOT_TOKEN: str
    KAFKA_BOOTSTRAP_SERVERS: str
    PROXY_URL: str

    # def get_db_url(self):
    #     return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
    #             f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
    model_config = SettingsConfigDict(env_file='.env')

    # def get_redis_url(self):
    #     return f'redis://{self.REDIS_URL}/0'

settings = Settings()