from pathlib import Path
import os
from pydantic import SecretStr

from utils import load_env


class Settings:
    token: SecretStr
    admins: list[int]  # format: "1821828 21891928 209219012 ..."
    static_folder: Path = Path("static")
    # model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    db_url: str = "sqlite+aiosqlite:///db.sqlite3"

    def __init__(self):
        load_env()
        self.token = SecretStr(os.environ.get('TOKEN'))
        self.admins = list(map(lambda x: int(x), os.environ.get('ADMINS').split(' ')))


config = Settings()
