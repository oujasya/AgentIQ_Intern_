"""Q23: settings read at startup; tokens are excluded from repr."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from agentiq.analysis import REFERENCE_AT
from agentiq.data import parse_utc


@dataclass(frozen=True)
class Settings:
    database_path: str = "data/agentiq.sqlite3"
    external_api_url: str = "https://example.invalid/records"
    api_token: str = field(default="", repr=False)
    reference_at: str = REFERENCE_AT
    handoff_threshold: int = 3

    def __post_init__(self):
        parse_utc(self.reference_at)
        if type(self.handoff_threshold) is not int or self.handoff_threshold < 0:
            raise ValueError("HANDOFF_THRESHOLD must be a non-negative integer")

    @classmethod
    def from_env(cls):
        load_dotenv(override=False)
        return cls(
            database_path=os.getenv("DATABASE_PATH", "data/agentiq.sqlite3"),
            external_api_url=os.getenv("EXTERNAL_API_URL", "https://example.invalid/records"),
            api_token=os.getenv("API_TOKEN", ""),
            reference_at=os.getenv("REFERENCE_AT", REFERENCE_AT),
            handoff_threshold=int(os.getenv("HANDOFF_THRESHOLD", "3")),
        )
