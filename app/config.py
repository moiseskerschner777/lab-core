from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    iris_host: str
    iris_port: int = 1972
    iris_namespace: str = "USER"
    iris_username: str
    iris_password: str


settings = Settings()
