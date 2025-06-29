from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import cryptography

class Settings(BaseSettings):
    bot_token: SecretStr
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    db_password: SecretStr

config = Settings()
