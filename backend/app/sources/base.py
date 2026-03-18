from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..config import get_settings


@dataclass
class SourceResult:
    source_name: str
    source_type: str
    items: list[dict[str, Any]] = field(default_factory=list)
    response_time_ms: int = 0
    error: str = ""


class BaseSource:
    name: str = "base"
    source_type: str = "unknown"
    default_enabled: bool = True

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        overrides = self.settings.enabled_overrides()
        return overrides.get(self.name, self.default_enabled)

    def fetch(self) -> SourceResult:
        raise NotImplementedError

    def _get(self, url: str) -> tuple[str, int]:
        headers = {
            "User-Agent": self.settings.app_fetch_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": self.settings.app_base_url,
            "Upgrade-Insecure-Requests": "1",
        }
        start = time.perf_counter()
        resp = requests.get(url, headers=headers, timeout=self.settings.app_source_timeout_seconds)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        resp.raise_for_status()
        return resp.text, elapsed_ms

    def _get_soup(self, url: str) -> tuple[BeautifulSoup, int]:
        text, elapsed = self._get(url)
        return BeautifulSoup(text, "html.parser"), elapsed