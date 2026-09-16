"""Discord Webhook publisher with structured executive embeds, smart chunking, and professional typography."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from src.core.config import Settings
from src.core.models import CTIAnalysisResult, IncidentItem
from src.publishers.base import BasePublisher

logger = logging.getLogger("nullday.publishers.discord")

# Sober Enterprise Color Codes (Decimal)
COLOR_CRITICAL_RED = 12597547    # #C0392B - Critical / Active KEV
COLOR_HIGH_ORANGE = 13849600     # #D35400 - High / Ransomware
COLOR_PURPLE = 8207512           # #7D3C98 - Elevated Threat
COLOR_DARK_NAVY = 2899536        # #2C3E50 - Routine / Weekly / Monthly
COLOR_DARK_BLUE = COLOR_DARK_NAVY


class DiscordPublisher(BasePublisher):
    """Formats and dual-publishes executive CTI reports to a Discord Webhook without emojis."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or Settings.DISCORD_WEBHOOK_URL

    def _determine_color(self, threat_level: str, has_kev: bool) -> int:
        """Select embed sidebar color based on severity and KEV status."""
        if has_kev or threat_level == "CRITICAL":
            return COLOR_CRITICAL_RED
        if threat_level == "HIGH":
            return COLOR_HIGH_ORANGE
        if threat_level == "ELEVATED":
            return COLOR_PURPLE
        return COLOR_DARK_NAVY

    def _build_overview_embed(self, data: CTIAnalysisResult) -> Dict[str, Any]:
        """Construct the header/overview embed summarizing the macro threat landscape."""
        report = data.discord_report
        has_kev = any(inc.kev_status for inc in report.incidents)
        color = self._determine_color(report.threat_level, has_kev)

        posture_label = {
            "CRITICAL": "THREAT POSTURE: CRITICAL // IMMEDIATE ACTION REQUIRED",
            "HIGH": "THREAT POSTURE: HIGH // ELEVATED THREAT ENVIRONMENT",
            "ELEVATED": "THREAT POSTURE: ELEVATED // ACTIVE MONITORING",
            "ROUTINE": "THREAT POSTURE: ROUTINE // BASELINE SURVEILLANCE",
        }.get(report.threat_level, "THREAT POSTURE: ACTIVE SURVEILLANCE")

        desc_parts = [
            f"**{posture_label}**\n",
            f"### Executive Summary\n{report.summary}\n",
        ]

        if report.strategic_analysis:
            desc_parts.append(f"### Strategic Threat Analysis\n{report.strategic_analysis}\n")

        description = "\n".join(desc_parts)
        if len(description) > 4000:
            description = description[:3997] + "..."

        fields = [
            {
                "name": "Incident Volume",
                "value": f"{len(report.incidents)} validated threat disclosures",
                "inline": True,
            },
            {
                "name": "Active KEV Disclosures",
                "value": f"{sum(1 for i in report.incidents if i.kev_status)} confirmed in-the-wild exploits",
                "inline": True,
            },
        ]

        return {
            "title": f"NULLDAY INTEL // {report.title.upper()}",
            "description": description,
            "color": color,
            "fields": fields,
            "footer": {
                "text": "NullDay Intel | Operational Cyber Threat Intelligence Briefing",
            },
        }

    def _build_recommendations_embed(self, recommendations: List[str], color: int) -> Optional[Dict[str, Any]]:
        """Construct an embed outlining strategic defensive directives if present."""
        if not recommendations:
            return None

        lines = [f"{i}. {rec}" for i, rec in enumerate(recommendations, 1)]
        desc = "The following prioritized directives are recommended for defensive posture alignment:\n\n" + "\n\n".join(lines)
        if len(desc) > 4000:
            desc = desc[:3997] + "..."

        return {
            "title": "STRATEGIC DEFENSIVE DIRECTIVES",
            "description": desc,
            "color": color,
            "footer": {
                "text": "NullDay Intel | Recommended Countermeasures",
            },
        }

    def _build_incident_embed(self, incident: IncidentItem, index: int, total: int) -> Dict[str, Any]:
        """Format an individual threat incident into a structured technical embed."""
        color = COLOR_CRITICAL_RED if incident.kev_status else COLOR_HIGH_ORANGE

        badge = "[CRITICAL EXPLOIT - KEV]" if incident.kev_status else "[SECURITY ADVISORY]"
        cve_str = f"`{incident.cve_id}`" if incident.cve_id else "`No CVE Assigned`"
        cvss_str = f"CVSS {incident.cvss}" if incident.cvss else "CVSS Evaluation Pending"

        fields = [
            {
                "name": "Target Sector & Technology",
                "value": incident.impact_sector[:250],
                "inline": True,
            },
            {
                "name": "Vulnerability Reference",
                "value": f"{cve_str} • {cvss_str}",
                "inline": True,
            },
            {
                "name": "Impact & Breach Assessment",
                "value": incident.estimated_damage[:250],
                "inline": False,
            },
            {
                "name": "Defensive Action & Remediation",
                "value": incident.mitigation[:1000],
                "inline": False,
            },
            {
                "name": "Verification & Reference",
                "value": f"[Originalquelle]({incident.source_url})",
                "inline": False,
            },
        ]

        title = f"{badge} Incident {index}/{total}: {incident.title}"
        if len(title) > 250:
            title = title[:247] + "..."

        return {
            "title": title,
            "color": color,
            "fields": fields,
        }

    def build_payload_batches(self, data: CTIAnalysisResult) -> List[Dict[str, Any]]:
        """Smart chunker respecting Discord's max 10 embeds and 5,500 char limits."""
        batches: List[Dict[str, Any]] = []
        current_embeds: List[Dict[str, Any]] = []
        current_chars = 0

        # 1. Overview Embed
        overview = self._build_overview_embed(data)
        current_embeds.append(overview)
        current_chars += len(overview.get("title", "")) + len(overview.get("description", ""))

        # 2. Recommendations Embed (if present)
        report = data.discord_report
        has_kev = any(inc.kev_status for inc in report.incidents)
        color = self._determine_color(report.threat_level, has_kev)
        rec_embed = self._build_recommendations_embed(report.key_recommendations, color)
        if rec_embed:
            rec_chars = len(rec_embed.get("title", "")) + len(rec_embed.get("description", ""))
            current_embeds.append(rec_embed)
            current_chars += rec_chars

        # 3. Incident Embeds
        total_incidents = len(report.incidents)
        for idx, inc in enumerate(report.incidents, 1):
            embed = self._build_incident_embed(inc, idx, total_incidents)
            embed_chars = len(embed.get("title", "")) + sum(
                len(f.get("name", "")) + len(f.get("value", "")) for f in embed.get("fields", [])
            )

            # Check if adding this embed exceeds 10 embeds or 5,200 characters
            if len(current_embeds) >= 10 or (current_chars + embed_chars) > 5200:
                batches.append({"embeds": current_embeds})
                current_embeds = [embed]
                current_chars = embed_chars
            else:
                current_embeds.append(embed)
                current_chars += embed_chars

        if current_embeds:
            batches.append({"embeds": current_embeds})

        return batches

    def publish(self, data: CTIAnalysisResult, dry_run: bool = False) -> bool:
        """Publish briefing embeds to Discord or print to stdout if dry-run."""
        batches = self.build_payload_batches(data)

        if dry_run or not self.webhook_url:
            print("\n" + "=" * 70)
            print("[DRY-RUN] DISCORD WEBHOOK EXECUTIVE BRIEFING PREVIEW")
            print("=" * 70)
            print(f"Total Batches / Dispatched Messages: {len(batches)}")
            for b_idx, batch in enumerate(batches, 1):
                print(f"\n--- Batch {b_idx}/{len(batches)} ({len(batch['embeds'])} embeds) ---")
                for e_idx, embed in enumerate(batch["embeds"], 1):
                    print(f"\n[Embed {e_idx}] Title: {embed.get('title')}")
                    if "description" in embed:
                        print(f"Description:\n{embed.get('description')}")
                    for f in embed.get("fields", []):
                        print(f"  • {f.get('name')}: {f.get('value')}")
            print("=" * 70 + "\n")
            return True

        # Live Webhook Execution
        logger.info(f"Dispatching {len(batches)} webhook payload(s) to Discord...")
        headers = {"Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=15) as client:
                for idx, batch in enumerate(batches, 1):
                    response = client.post(self.webhook_url, json=batch, headers=headers)
                    if response.status_code not in (200, 204):
                        logger.error(
                            f"Discord webhook error in batch {idx}: HTTP {response.status_code} - {response.text}"
                        )
                        return False
                    logger.info(f"Successfully posted Discord batch {idx}/{len(batches)}.")
            return True
        except Exception as e:
            logger.error(f"Failed to transmit Discord webhook: {e}", exc_info=True)
            return False
