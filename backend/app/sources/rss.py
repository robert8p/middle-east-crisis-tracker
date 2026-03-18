from __future__ import annotations

import feedparser

from .base import BaseSource, SourceResult
from ..utils.time import parse_dt
from ..utils.text import normalise_space


class RssSource(BaseSource):
    url: str = ""
    source_label: str = ""

    def fetch(self) -> SourceResult:
        result = SourceResult(source_name=self.name, source_type=self.source_type)
        if not self.enabled:
            return result
        try:
            text, elapsed = self._get(self.url)
            feed = feedparser.parse(text)
            items = []
            for entry in feed.entries[: self.settings.app_max_items_per_source]:
                title = normalise_space(getattr(entry, "title", ""))
                link = getattr(entry, "link", "")
                summary = normalise_space(getattr(entry, "summary", "") or getattr(entry, "description", ""))
                published = parse_dt(
                    getattr(entry, "published", None)
                    or getattr(entry, "updated", None)
                    or getattr(entry, "pubDate", None)
                )
                items.append(
                    {
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "published_at_utc": published,
                        "source": self.source_label or self.name,
                        "source_type": self.source_type,
                    }
                )
            result.items = items
            result.response_time_ms = elapsed
            return result
        except Exception as exc:
            result.error = str(exc)
            return result