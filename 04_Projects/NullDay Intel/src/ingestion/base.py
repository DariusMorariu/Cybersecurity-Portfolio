"""Abstract base class and utilities for feed ingestion."""

from abc import ABC, abstractmethod
import hashlib
import re
from typing import List
from src.core.models import RawArticle

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def generate_article_id(url: str, title: str = "") -> str:
    """Generate deterministic SHA-256 hash for deduplication."""
    clean_url = url.strip().split("#")[0].rstrip("/")
    if not clean_url and title:
        key = title.strip().lower()
    else:
        key = clean_url.lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def extract_cves(text: str) -> List[str]:
    """Extract and deduplicate all CVE identifiers from text."""
    if not text:
        return []
    matches = CVE_PATTERN.findall(text)
    # Deduplicate while preserving uppercase format
    return list(dict.fromkeys(m.upper() for m in matches))


class BaseFeedFetcher(ABC):
    """Interface for CTI feed fetchers."""

    def __init__(self, source_id: str, name: str, url: str, timeout: int = 15):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.timeout = timeout

    @abstractmethod
    def fetch(self, hours_lookback: int) -> List[RawArticle]:
        """Fetch and return articles published within the lookback window."""
        pass
