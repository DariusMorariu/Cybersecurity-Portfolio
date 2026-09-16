"""SQLite state persistence and deduplication storage for NullDay Intel."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set
import logging

from src.core.models import RawArticle

logger = logging.getLogger("nullday.storage")


class IntelDatabase:
    """Manages processed article hashes and run history to prevent duplicate alerts."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_items (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    cve_id TEXT,
                    published_at TEXT,
                    processed_at TEXT NOT NULL,
                    run_mode TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_processed_url ON processed_items(url)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_items(processed_at)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT NOT NULL,
                    run_timestamp TEXT NOT NULL,
                    items_fetched INTEGER NOT NULL,
                    items_new INTEGER NOT NULL,
                    threat_level TEXT,
                    status TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def is_processed(self, item_id: str) -> bool:
        """Check if an article hash has already been processed."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_items WHERE id = ?", (item_id,)
            )
            return cursor.fetchone() is not None

    def get_processed_ids(self) -> Set[str]:
        """Return all processed item IDs in the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id FROM processed_items")
            return {row["id"] for row in cursor.fetchall()}

    def filter_unprocessed(self, items: List[RawArticle]) -> List[RawArticle]:
        """Filter out any items that have already been processed in prior runs."""
        processed_ids = self.get_processed_ids()
        unprocessed = [item for item in items if item.id not in processed_ids]
        logger.info(
            f"Deduplication check: {len(unprocessed)} new of {len(items)} total fetched."
        )
        return unprocessed

    def mark_processed(self, items: List[RawArticle], mode: str) -> None:
        """Record newly processed articles in the database."""
        if not items:
            return

        now_str = datetime.now(timezone.utc).isoformat()
        records = [
            (
                item.id,
                item.url,
                item.title,
                ",".join(item.cve_candidates) if item.cve_candidates else None,
                item.published_at.isoformat(),
                now_str,
                mode,
            )
            for item in items
        ]

        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO processed_items
                (id, url, title, cve_id, published_at, processed_at, run_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            conn.commit()
        logger.info(f"Marked {len(records)} items as processed in state database.")

    def record_run(
        self,
        mode: str,
        items_fetched: int,
        items_new: int,
        threat_level: Optional[str] = None,
        status: str = "SUCCESS",
    ) -> None:
        """Log pipeline execution metadata."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO execution_runs
                (mode, run_timestamp, items_fetched, items_new, threat_level, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (mode, now_str, items_fetched, items_new, threat_level, status),
            )
            conn.commit()

    def get_stats(self) -> dict:
        """Return high-level persistence statistics."""
        with self._get_connection() as conn:
            total_items = conn.execute(
                "SELECT COUNT(*) AS cnt FROM processed_items"
            ).fetchone()["cnt"]
            total_runs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM execution_runs"
            ).fetchone()["cnt"]
            return {"total_processed_items": total_items, "total_runs": total_runs}
