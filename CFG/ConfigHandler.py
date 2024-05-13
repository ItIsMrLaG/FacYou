from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    token: SecretStr
    admins: list[int]
    static_folder: Path = Path("static")
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    db_url: str = "sqlite+aiosqlite:///db.sqlite3"


config = Settings()
