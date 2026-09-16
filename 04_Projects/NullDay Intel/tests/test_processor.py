"""Tests for LLM processor and Pydantic structured output models."""

from datetime import datetime, timezone
from src.core.models import (
    CTIAnalysisResult,
    DiscordReport,
    IncidentItem,
    RawArticle,
    XPayload,
)
from src.core.processor import CTIProcessor


def test_cti_models_validation():
    incident = IncidentItem(
        title="Critical RCE in Ivanti Connect Secure",
        cve_id="CVE-2026-1111",
        cvss=9.8,
        kev_status=True,
        impact_sector="Enterprise VPN & Zero Trust Gateways",
        estimated_damage="Financial Impact: Undisclosed / Under Investigation",
        mitigation="Apply security patch release 22.7R2 immediately.",
        source_url="https://cisa.gov/example",
    )
    assert incident.cve_id == "CVE-2026-1111"
    assert incident.cvss == 9.8
    assert incident.kev_status is True

    result = CTIAnalysisResult(
        discord_report=DiscordReport(
            summary="Multiple zero-day vulnerabilities observed actively targeted.",
            threat_level="CRITICAL",
            incidents=[incident],
        ),
        x_payload=XPayload(
            tweet_text="🚨 ALERT: Critical RCE in Ivanti Connect Secure (CVE-2026-1111) CVSS 9.8 actively exploited in the wild. #ThreatIntel #CyberSecurity #CVE",
            thread_reply="Mitigation: Patch immediately to release 22.7R2. Link: https://cisa.gov/example",
        ),
    )

    assert len(result.x_payload.tweet_text) <= 260
    assert len(result.x_payload.thread_reply) <= 280
    assert result.discord_report.threat_level == "CRITICAL"


def test_processor_mock_fallback():
    now = datetime.now(timezone.utc)
    articles = [
        RawArticle(
            id="art_1",
            source_id="cisa",
            source_name="CISA KEV",
            title="Active Exploitation of PAN-OS Firewall",
            url="https://example.com/panos",
            published_at=now,
            summary="Attackers bypassing authentication.",
            cve_candidates=["CVE-2026-2222"],
            is_kev=True,
        )
    ]

    # Initialize without API key -> uses mock fallback
    processor = CTIProcessor(api_key=None)
    result = processor.process(articles, mode="daily")

    assert isinstance(result, CTIAnalysisResult)
    assert len(result.discord_report.incidents) >= 1
    assert result.discord_report.threat_level == "CRITICAL"
    assert len(result.x_payload.tweet_text) <= 260


def test_system_prompt_template_rendering():
    from src.core.processor import SYSTEM_PROMPT_TEMPLATE
    for mode in ["daily", "weekly", "monthly"]:
        rendered = SYSTEM_PROMPT_TEMPLATE.replace("{mode}", mode)
        assert mode in rendered
        assert "{mode}" not in rendered
        # Ensure no accidental format placeholders like {System/CVE} remain unescaped
        assert "{System/CVE}" not in rendered
        assert "{Link}" not in rendered
