"""Tests for Discord and X/Twitter publishers."""

from src.core.models import (
    CTIAnalysisResult,
    DiscordReport,
    IncidentItem,
    XPayload,
)
from src.publishers.discord import DiscordPublisher, COLOR_CRITICAL_RED, COLOR_DARK_BLUE
from src.publishers.x_twitter import XPublisher


def _sample_analysis(count=3, kev=True) -> CTIAnalysisResult:
    incidents = [
        IncidentItem(
            title=f"Security Incident #{i}",
            cve_id=f"CVE-2026-000{i}",
            cvss=9.0 if i == 1 else 7.5,
            kev_status=(i == 1 and kev),
            impact_sector="Financial Services / Banking",
            estimated_damage="Financial Impact: Undisclosed / Under Investigation",
            mitigation="Restrict network ports and update firmware.",
            source_url=f"https://example.com/advisory-{i}",
        )
        for i in range(1, count + 1)
    ]
    return CTIAnalysisResult(
        discord_report=DiscordReport(
            title="NullDay Intel // Daily Cyber Threat Briefing",
            summary="High activity targeting critical enterprise perimeters.",
            threat_level="CRITICAL" if kev else "ROUTINE",
            incidents=incidents,
        ),
        x_payload=XPayload(
            tweet_text="🚨 ALERT: Critical exploit reported in perimeter services. Immediate patching required. #ThreatIntel #CyberSecurity #CVE",
            thread_reply="Mitigations: Restrict ports and apply vendor updates. Ref: https://example.com/1",
        ),
    )


def test_discord_chunker_and_colors():
    data = _sample_analysis(count=3, kev=True)
    publisher = DiscordPublisher(webhook_url=None)
    batches = publisher.build_payload_batches(data)

    assert len(batches) == 1
    # 1 overview embed + 3 incident embeds = 4 embeds
    assert len(batches[0]["embeds"]) == 4

    # Overview embed color should be red because of KEV
    assert batches[0]["embeds"][0]["color"] == COLOR_CRITICAL_RED

    # Incident 1 embed should also be red (kev_status=True)
    assert batches[0]["embeds"][1]["color"] == COLOR_CRITICAL_RED


def test_discord_large_batch_splitting():
    # Generate 15 incidents to force multi-batch splitting (max 10 embeds per message)
    data = _sample_analysis(count=15, kev=False)
    publisher = DiscordPublisher(webhook_url=None)
    batches = publisher.build_payload_batches(data)

    # Must split across at least 2 webhook messages
    assert len(batches) >= 2
    for b in batches:
        assert len(b["embeds"]) <= 10


def test_discord_dry_run_execution():
    data = _sample_analysis(count=1, kev=False)
    publisher = DiscordPublisher(webhook_url=None)
    assert publisher.publish(data, dry_run=True) is True


def test_x_publisher_dry_run_execution():
    data = _sample_analysis(count=1, kev=True)
    publisher = XPublisher()
    assert publisher.publish(data, dry_run=True) is True
