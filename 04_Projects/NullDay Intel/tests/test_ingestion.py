"""Tests for ingestion parsers and utilities."""

from datetime import datetime, timezone
from src.ingestion.base import generate_article_id, extract_cves
from src.core.models import RawArticle


def test_generate_article_id():
    url1 = "https://example.com/advisory-1"
    url2 = "https://example.com/advisory-1#section-a"
    url3 = "https://example.com/advisory-2"

    # Fragment stripping should ensure identical IDs
    assert generate_article_id(url1) == generate_article_id(url2)
    assert generate_article_id(url1) != generate_article_id(url3)


def test_extract_cves():
    text = (
        "Advisory details for CVE-2026-1234 and CVE-2024-56789. "
        "Also duplicate reference cve-2026-1234 in the body."
    )
    cves = extract_cves(text)
    assert len(cves) == 2
    assert "CVE-2026-1234" in cves
    assert "CVE-2024-56789" in cves


def test_raw_article_model():
    now = datetime.now(timezone.utc)
    art = RawArticle(
        id="test_id_123",
        source_id="bleeping_computer",
        source_name="BleepingComputer",
        title="Zero-Day in Cisco Routers",
        url="https://bleepingcomputer.com/news/1",
        published_at=now,
        summary="Cisco fixed an actively exploited flaw.",
        cve_candidates=["CVE-2026-0001"],
        is_kev=True,
    )
    assert art.is_kev is True
    assert art.cve_candidates == ["CVE-2026-0001"]
