"""Run settings, read from environment variables or a local .env file."""
import os
from dataclasses import dataclass, field
from urllib.parse import urlencode

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://qae-assignment-tau.vercel.app"


@dataclass(frozen=True)
class Settings:
    base_url: str
    user_id: str = field(repr=False)  # kept out of tracebacks and CI logs
    headless: bool
    timeout: float

    @classmethod
    def from_env(cls) -> "Settings":
        # Read on first use, not at import, so tests can be collected without credentials.
        load_dotenv()
        user_id = os.getenv("USER_ID", "").strip()
        if not user_id:
            raise RuntimeError("USER_ID is not set. Copy .env.example to .env and fill it in.")
        return cls(
            base_url=os.getenv("BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            user_id=user_id,
            headless=os.getenv("HEADLESS", "true").strip().lower() != "false",
            timeout=float(os.getenv("TIMEOUT", "15")),
        )

    @property
    def app_url(self) -> str:
        return f"{self.base_url}/?{urlencode({'user-id': self.user_id})}"
