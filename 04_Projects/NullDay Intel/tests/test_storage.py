"""Tests for SQLite persistence and deduplication."""

from datetime import datetime, timezone
import pytest
from src.core.models import RawArticle
from src.storage.database import IntelDatabase


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_intel.db"
    return IntelDatabase(db_file)


def test_db_initialization(temp_db):
    stats = temp_db.get_stats()
    assert stats["total_processed_items"] == 0
    assert stats["total_runs"] == 0


def test_mark_and_filter_processed(temp_db):
    now = datetime.now(timezone.utc)
    art1 = RawArticle(
        id="hash_001",
        source_id="test",
        source_name="Test Source",
        title="Critical Vulnerability in Fortinet",
        url="https://example.com/1",
        published_at=now,
        summary="Remote code execution detected.",
        cve_candidates=["CVE-2026-9999"],
        is_kev=True,
    )
    art2 = RawArticle(
        id="hash_002",
        source_id="test",
        source_name="Test Source",
        title="Ransomware attack on Hospital",
        url="https://example.com/2",
        published_at=now,
        summary="Data extortion ongoing.",
        cve_candidates=[],
        is_kev=False,
    )

    # Initially, both are unprocessed
    unprocessed = temp_db.filter_unprocessed([art1, art2])
    assert len(unprocessed) == 2

    # Mark art1 as processed
    temp_db.mark_processed([art1], mode="daily")
    assert temp_db.is_processed("hash_001") is True
    assert temp_db.is_processed("hash_002") is False

    # Now, only art2 should remain unprocessed
    unprocessed_second = temp_db.filter_unprocessed([art1, art2])
    assert len(unprocessed_second) == 1
    assert unprocessed_second[0].id == "hash_002"


def test_record_run(temp_db):
    temp_db.record_run(
        mode="daily",
        items_fetched=10,
        items_new=2,
        threat_level="CRITICAL",
        status="SUCCESS",
    )
    stats = temp_db.get_stats()
    assert stats["total_runs"] == 1
