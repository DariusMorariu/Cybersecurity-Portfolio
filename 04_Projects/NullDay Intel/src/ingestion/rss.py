"""RSS and Atom feed ingestor for NullDay Intel."""

from datetime import datetime, timezone, timedelta
import email.utils
import logging
import time
from typing import List, Optional
import feedparser
import httpx

from src.core.models import RawArticle
from src.ingestion.base import BaseFeedFetcher, generate_article_id, extract_cves

logger = logging.getLogger("nullday.ingestion.rss")


class RSSFetcher(BaseFeedFetcher):
    """Fetches and normalizes articles from standard RSS/Atom feeds."""

    def _parse_date(self, entry: dict) -> Optional[datetime]:
        """Attempt to parse publication date from various RSS field formats."""
        # 1. feedparser parsed time struct
        for field in ("published_parsed", "updated_parsed", "created_parsed"):
            val = entry.get(field)
            if val:
                try:
                    return datetime.fromtimestamp(time.mktime(val), tz=timezone.utc)
                except Exception:
                    pass

        # 2. RFC 2822 / RFC 822 string date
        for field in ("published", "updated", "pubDate", "dc:date"):
            raw_str = entry.get(field)
            if raw_str and isinstance(raw_str, str):
                try:
                    parsed_tuple = email.utils.parsedate_to_datetime(raw_str)
                    if parsed_tuple.tzinfo is None:
                        return parsed_tuple.replace(tzinfo=timezone.utc)
                    return parsed_tuple.astimezone(timezone.utc)
                except Exception:
                    pass

                # ISO 8601 fallback
                try:
                    dt = datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        return dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc)
                except Exception:
                    pass

        return None

    def fetch(self, hours_lookback: int) -> List[RawArticle]:
        """Fetch RSS feed and filter items within the specified hours window."""
        articles: List[RawArticle] = []
        now_utc = datetime.now(timezone.utc)
        cutoff_time = now_utc - timedelta(hours=hours_lookback)

        headers = {
            "User-Agent": "NullDayIntel-CTI/1.0 (+https://github.com/DariusMorariu/Cybersecurity-Portfolio)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                response = client.get(self.url)
                response.raise_for_status()
                content = response.content
        except Exception as e:
            logger.warning(f"Failed to retrieve RSS feed from {self.name} ({self.url}): {e}")
            return []

        try:
            feed = feedparser.parse(content)
        except Exception as e:
            logger.warning(f"Failed to parse RSS XML from {self.name}: {e}")
            return []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not link or not title:
                continue

            pub_date = self._parse_date(entry)
            # If publication date cannot be parsed, default to current time for safety
            if not pub_date:
                pub_date = now_utc

            # Filter by time window
            if pub_date < cutoff_time:
                continue

            summary = entry.get("summary", "") or entry.get("description", "")
            # Basic cleanup of summary text
            clean_summary = summary.replace("<p>", "").replace("</p>", "\n").strip()
            if len(clean_summary) > 1000:
                clean_summary = clean_summary[:1000] + "..."

            combined_text = f"{title} {clean_summary}"
            cves = extract_cves(combined_text)

            article = RawArticle(
                id=generate_article_id(link, title),
                source_id=self.source_id,
                source_name=self.name,
                title=title,
                url=link,
                published_at=pub_date,
                summary=clean_summary,
                cve_candidates=cves,
                is_kev=False,
            )
            articles.append(article)

        logger.info(
            f"Source '{self.name}': found {len(articles)} articles within {hours_lookback}h window."
        )
        return articles
