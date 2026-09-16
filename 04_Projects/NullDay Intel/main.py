#!/usr/bin/env python3
"""NullDay Intel - Serverless Cyber Threat Intelligence (CTI) Briefing Engine.

CLI Entrypoint supporting daily, weekly, and monthly briefing modes with dual-publishing
to Discord and X/Twitter.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Windows UTF-8 output for emojis and special characters
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.core.config import Settings, SOURCES_CONFIG_PATH, DB_PATH, TIME_WINDOWS_HOURS
from src.core.processor import CTIProcessor
from src.ingestion.aggregator import FeedAggregator
from src.publishers.discord import DiscordPublisher
from src.publishers.x_twitter import XPublisher
from src.storage.database import IntelDatabase


def setup_logging(level_name: str = "INFO") -> None:
    """Configure structured logging output."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NullDay Intel - Serverless Cyber Threat Intelligence Briefing Engine"
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Briefing scope and time-window (default: daily)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute pipeline without dispatching live API calls to Discord or X",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass database deduplication check (useful for testing)",
    )
    parser.add_argument(
        "--sources-path",
        type=Path,
        default=SOURCES_CONFIG_PATH,
        help="Custom path to sources.yaml configuration",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help="Custom path to SQLite state persistence database",
    )

    args = parser.parse_args()
    setup_logging(Settings.LOG_LEVEL)
    logger = logging.getLogger("nullday.main")

    logger.info("=" * 60)
    logger.info(f"Starting NullDay Intel // Mode: {args.mode.upper()} | Dry-Run: {args.dry_run}")
    logger.info("=" * 60)

    # 1. Initialize Storage
    db = IntelDatabase(args.db_path)

    # 2. Ingest & Deduplicate Feeds
    lookback_hours = TIME_WINDOWS_HOURS.get(args.mode, 26)
    aggregator = FeedAggregator(sources_config_path=args.sources_path, db=db)
    raw_articles = aggregator.aggregate(hours_lookback=lookback_hours, force=args.force)

    logger.info(f"Ready to process {len(raw_articles)} threat items.")

    # 3. Analyze with Google GenAI SDK
    processor = CTIProcessor()
    analysis_result = processor.process(raw_articles, mode=args.mode)

    # 4. Dual-Publishing
    discord_pub = DiscordPublisher()
    x_pub = XPublisher()

    logger.info("Executing Dual-Publishing Engine...")
    discord_ok = discord_pub.publish(analysis_result, dry_run=args.dry_run)
    x_ok = x_pub.publish(analysis_result, dry_run=args.dry_run)

    overall_ok = discord_ok and x_ok

    # 5. State Persistence
    if not args.dry_run and overall_ok:
        db.mark_processed(raw_articles, mode=args.mode)
        db.record_run(
            mode=args.mode,
            items_fetched=len(raw_articles),
            items_new=len(raw_articles),
            threat_level=analysis_result.discord_report.threat_level,
            status="SUCCESS",
        )
        logger.info("State database updated and run recorded.")
    elif args.dry_run:
        logger.info("[Dry-Run Complete] Database state changes skipped.")

    if not overall_ok:
        logger.error("Pipeline encountered errors during publishing.")
        return 1

    logger.info("NullDay Intel execution completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
