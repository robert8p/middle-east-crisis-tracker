from __future__ import annotations

import hashlib
import re
from typing import Iterable

STOPWORDS = {
    "the", "and", "a", "an", "of", "to", "for", "on", "in", "at", "with", "by", "from",
    "as", "is", "are", "was", "were", "be", "this", "that", "it", "or", "over", "into",
    "after", "amid", "new", "latest", "update", "statement", "press", "release", "says",
}

def normalise_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def slug_hash(value: str) -> str:
    return hashlib.sha1(normalise_space(value).lower().encode("utf-8")).hexdigest()[:20]

def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-]+", (text or "").lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def fingerprint(text: str, extras: list[str] | None = None) -> str:
    base = " ".join(sorted(set(tokenize(text) + (extras or []))))
    return slug_hash(base)