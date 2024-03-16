from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    petitlink_email: str
    petitlink_email_pass: str
    petitlink_email_secret_key: str
    petitlink_email_salt: str


settings = Settings()