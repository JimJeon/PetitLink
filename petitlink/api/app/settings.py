from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    petitlink_length: int = 5


settings = Settings()