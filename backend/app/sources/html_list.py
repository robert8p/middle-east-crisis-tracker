from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseSource, SourceResult
from ..utils.time import parse_dt
from ..utils.text import normalise_space


@dataclass
class HtmlListConfig:
    url: str
    item_selector: str
    title_selector: str
    link_selector: str
    date_selector: str | None = None
    summary_selector: str | None = None
    source_label: str = ""


class HtmlListSource(BaseSource):
    config: HtmlListConfig

    def _is_valid_item(self, title: str, link: str) -> bool:
        lowered_title = (title or "").strip().lower()
        lowered_link = (link or "").strip().lower()
        if not lowered_title or len(lowered_title) < 4:
            return False
        if not lowered_link:
            return False
        if lowered_link in {"#", "javascript:void(0);"}:
            return False
        if lowered_link.startswith("javascript:") or lowered_link.startswith("mailto:"):
            return False
        if "getlink(item.link)" in lowered_link:
            return False
        blocked_titles = {
            "about us", "overview", "minister", "farsi", "فارسی", "عربی", "arabic",
            "iri flag", "iri national anthem"
        }
        if lowered_title in blocked_titles:
            return False
        return True

    def parse_items(self, soup: BeautifulSoup) -> list[dict]:
        items: list[dict] = []
        candidates = soup.select(self.config.item_selector)
        for item in candidates:
            if len(items) >= self.settings.app_max_items_per_source:
                break
            title_node = item.select_one(self.config.title_selector)
            link_node = item.select_one(self.config.link_selector)
            if not title_node or not link_node:
                continue
            title = normalise_space(title_node.get_text(" ", strip=True))
            link = urljoin(self.config.url, link_node.get("href", "").strip())
            if not self._is_valid_item(title, link):
                continue
            date_value = ""
            if self.config.date_selector:
                node = item.select_one(self.config.date_selector)
                if node:
                    date_value = node.get_text(" ", strip=True)
            summary = ""
            if self.config.summary_selector:
                node = item.select_one(self.config.summary_selector)
                if node:
                    summary = normalise_space(node.get_text(" ", strip=True))
            items.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published_at_utc": parse_dt(date_value),
                    "source": self.config.source_label or self.name,
                    "source_type": self.source_type,
                }
            )
        return items

    def fetch(self) -> SourceResult:
        result = SourceResult(source_name=self.name, source_type=self.source_type)
        if not self.enabled:
            return result
        try:
            soup, elapsed = self._get_soup(self.config.url)
            result.items = self.parse_items(soup)
            result.response_time_ms = elapsed
            return result
        except Exception as exc:
            result.error = str(exc)
            return result