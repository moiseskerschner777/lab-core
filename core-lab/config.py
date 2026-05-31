from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    iris_host: str
    iris_port: int = 1972
    iris_namespace: str = "USER"
    iris_username: str
    iris_password: str


settings = Settings()
