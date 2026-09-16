"""CISA Known Exploited Vulnerabilities (KEV) catalog ingestor."""

from datetime import datetime, timezone, timedelta
import logging
from typing import List
import httpx

from src.core.models import RawArticle
from src.ingestion.base import BaseFeedFetcher, generate_article_id

logger = logging.getLogger("nullday.ingestion.cisa_kev")


class CISAKEVFetcher(BaseFeedFetcher):
    """Fetches newly added entries from the official CISA KEV JSON catalog."""

    def fetch(self, hours_lookback: int) -> List[RawArticle]:
        """Fetch KEV catalog and return vulnerabilities added within the lookback window."""
        articles: List[RawArticle] = []
        now_utc = datetime.now(timezone.utc)
        cutoff_date = (now_utc - timedelta(hours=hours_lookback)).date()

        headers = {
            "User-Agent": "NullDayIntel-CTI/1.0 (+https://github.com/DariusMorariu/Cybersecurity-Portfolio)",
            "Accept": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                response = client.get(self.url)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch CISA KEV catalog from {self.url}: {e}")
            return []

        vulnerabilities = data.get("vulnerabilities", [])
        for item in vulnerabilities:
            date_added_str = item.get("dateAdded")
            if not date_added_str:
                continue

            try:
                date_added = datetime.strptime(date_added_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            # Check if added within the lookback window
            if date_added < cutoff_date:
                continue

            cve_id = item.get("cveID", "").strip().upper()
            vendor = item.get("vendorProject", "Unknown Vendor")
            product = item.get("product", "Unknown Product")
            vuln_name = item.get("vulnerabilityName", "Active Exploitation Detected")
            desc = item.get("shortDescription", "")
            action = item.get("requiredAction", "")
            ransomware = item.get("knownRansomwareCampaignUse", "Unknown")

            title = f"[CISA KEV] {cve_id}: {vendor} {product} Exploitation Alert"
            url = f"https://nvd.nist.gov/vuln/detail/{cve_id}" if cve_id else self.url
            summary = (
                f"Vulnerability: {vuln_name}\n"
                f"Description: {desc}\n"
                f"Required Action: {action}\n"
                f"Known Ransomware Use: {ransomware}"
            )

            # Publication datetime at midnight UTC of dateAdded
            pub_dt = datetime(date_added.year, date_added.month, date_added.day, tzinfo=timezone.utc)

            article = RawArticle(
                id=generate_article_id(url, cve_id or title),
                source_id=self.source_id,
                source_name=self.name,
                title=title,
                url=url,
                published_at=pub_dt,
                summary=summary,
                cve_candidates=[cve_id] if cve_id else [],
                is_kev=True,
            )
            articles.append(article)

        logger.info(
            f"CISA KEV: found {len(articles)} vulnerabilities added within {hours_lookback}h."
        )
        return articles
