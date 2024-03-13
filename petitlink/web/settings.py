from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    email_secret_key: str
    email_salt: str


settings = Settings()