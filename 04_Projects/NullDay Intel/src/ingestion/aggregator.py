"""Aggregator orchestrating concurrent CTI feed ingestion and deduplication."""

import logging
from pathlib import Path
from typing import List, Optional
import yaml

from src.core.models import RawArticle
from src.ingestion.base import BaseFeedFetcher
from src.ingestion.cisa_kev import CISAKEVFetcher
from src.ingestion.rss import RSSFetcher
from src.storage.database import IntelDatabase

logger = logging.getLogger("nullday.ingestion.aggregator")


class FeedAggregator:
    """Loads configured feeds, runs ingestion, and deduplicates against local SQLite state."""

    def __init__(self, sources_config_path: Path, db: Optional[IntelDatabase] = None):
        self.sources_config_path = Path(sources_config_path)
        self.db = db
        self.fetchers: List[BaseFeedFetcher] = []
        self._load_sources()

    def _load_sources(self) -> None:
        """Parse sources.yaml and instantiate appropriate fetchers."""
        if not self.sources_config_path.exists():
            raise FileNotFoundError(f"Sources configuration not found at {self.sources_config_path}")

        with open(self.sources_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        settings = data.get("settings", {})
        timeout = settings.get("request_timeout_seconds", 15)

        for src in data.get("sources", []):
            if not src.get("enabled", True):
                continue

            src_type = src.get("type", "rss")
            src_id = src.get("id")
            name = src.get("name")
            url = src.get("url")

            if src_type == "cisa_json":
                self.fetchers.append(CISAKEVFetcher(source_id=src_id, name=name, url=url, timeout=timeout))
            elif src_type == "rss":
                self.fetchers.append(RSSFetcher(source_id=src_id, name=name, url=url, timeout=timeout))
            else:
                logger.warning(f"Unknown feed type '{src_type}' for source '{name}'. Skipping.")

        logger.info(f"Loaded {len(self.fetchers)} active CTI feed fetchers.")

    def aggregate(self, hours_lookback: int, force: bool = False) -> List[RawArticle]:
        """Fetch all feeds and filter out duplicates using SQLite state."""
        all_articles: List[RawArticle] = []

        for fetcher in self.fetchers:
            try:
                items = fetcher.fetch(hours_lookback=hours_lookback)
                all_articles.extend(items)
            except Exception as e:
                logger.error(f"Error fetching from {fetcher.name}: {e}", exc_info=True)

        logger.info(f"Aggregated {len(all_articles)} total articles across all feeds.")

        # In-memory deduplication by article ID
        seen_ids = set()
        deduped: List[RawArticle] = []
        for art in all_articles:
            if art.id not in seen_ids:
                seen_ids.add(art.id)
                deduped.append(art)

        # Database deduplication
        if self.db and not force:
            unprocessed = self.db.filter_unprocessed(deduped)
        else:
            unprocessed = deduped

        # Sort: KEV articles first, then newest publication date
        unprocessed.sort(key=lambda x: (x.is_kev, x.published_at), reverse=True)
        return unprocessed
