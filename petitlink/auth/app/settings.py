from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    auth_email: str
    auth_email_password: str
    auth_secret_key: str
    auth_salt: str
    auth_access_token_secret_key: str


settings = Settings()