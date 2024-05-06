from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    token: SecretStr
    static_folder: Path = Path("static")
    model_config = SettingsConfigDict(env_file='./.env', env_file_encoding='utf-8')


config = Settings()
