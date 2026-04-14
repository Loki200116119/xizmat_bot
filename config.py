"""
⚙️ Konfiguratsiya — barcha sozlamalar bir joyda
"""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")
    GOOGLE_API_KEY: str = ""
    ADMIN_IDS: List[int] = Field(default_factory=list)

    BOT_NAME: str = "XizmatBot"
    COMPANY_NAME: str = "Altron"
    COMPANY_PHONE: str = "+998 95 494 44 66"
    COMPANY_ADDRESS: str = "Toshkent, O'zbekiston"
    COMPANY_HOURS: str = "Du-Ju: 09:00–18:00"
    COMPANY_USERNAME: str = "@Lochinsafarov"

    DATABASE_URL: str = "sqlite+aiosqlite:///./bot_data.db"
    MAX_ORDERS_PER_PAGE: int = 5

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            v = v.replace("[", "").replace("]", "")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()