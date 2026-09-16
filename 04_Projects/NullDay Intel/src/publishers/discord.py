"""Discord Webhook publisher with rich embeds, smart chunking, and color coding."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from src.core.config import Settings
from src.core.models import CTIAnalysisResult, IncidentItem
from src.publishers.base import BasePublisher

logger = logging.getLogger("nullday.publishers.discord")

# Color Codes (Decimal)
COLOR_CRITICAL_RED = 15548997    # #ED4245 - Critical / Active KEV
COLOR_HIGH_ORANGE = 15105570     # #E67E22 - High / Ransomware
COLOR_DARK_BLUE = 3426654        # #34495E - Weekly / Monthly / Routine
COLOR_PURPLE = 10181046          # #9B59B6 - Elevated Threat


class DiscordPublisher(BasePublisher):
    """Formats and dual-publishes executive CTI reports to a Discord Webhook."""

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
        return COLOR_DARK_BLUE

    def _build_overview_embed(self, data: CTIAnalysisResult) -> Dict[str, Any]:
        """Construct the header/overview embed summarizing the run."""
        report = data.discord_report
        has_kev = any(inc.kev_status for inc in report.incidents)
        color = self._determine_color(report.threat_level, has_kev)

        threat_emoji = {
            "CRITICAL": "🔴 CRITICAL THREAT",
            "HIGH": "🟠 HIGH THREAT",
            "ELEVATED": "🟣 ELEVATED THREAT",
            "ROUTINE": "🔵 ROUTINE MONITORING",
        }.get(report.threat_level, "🟡 ACTIVE ADVISORY")

        description = (
            f"**Posture Assessment:** {threat_emoji}\n\n"
            f"{report.summary}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        if len(description) > 4000:
            description = description[:3997] + "..."

        return {
            "title": f"🛡️ {report.title}",
            "description": description,
            "color": color,
            "fields": [
                {
                    "name": "📊 Monitored Incidents",
                    "value": f"{len(report.incidents)} threats analyzed in this cycle",
                    "inline": True,
                },
                {
                    "name": "🚨 KEV Alerts",
                    "value": f"{sum(1 for i in report.incidents if i.kev_status)} active 0-day / in-the-wild exploits",
                    "inline": True,
                },
            ],
            "footer": {
                "text": "NullDay Intel • Automated Cyber Threat Briefing Engine",
            },
        }

    def _build_incident_embed(self, incident: IncidentItem, index: int, total: int) -> Dict[str, Any]:
        """Format an individual threat incident into a structured rich embed."""
        color = COLOR_CRITICAL_RED if incident.kev_status else COLOR_HIGH_ORANGE

        badge = "🚨 [ACTIVE EXPLOIT / KEV]" if incident.kev_status else "⚠️ [THREAT ADVISORY]"
        cve_str = f"`{incident.cve_id}`" if incident.cve_id else "`No CVE Assigned`"
        cvss_str = f"CVSS {incident.cvss}" if incident.cvss else "CVSS Pending"

        fields = [
            {
                "name": "🎯 Target / Impact Sector",
                "value": incident.impact_sector[:250],
                "inline": True,
            },
            {
                "name": "⚡ Severity & Identifier",
                "value": f"{cve_str} • {cvss_str}",
                "inline": True,
            },
            {
                "name": "💰 Estimated Impact / Damage",
                "value": incident.estimated_damage[:250],
                "inline": False,
            },
            {
                "name": "🛡️ Defensive Action & Mitigation",
                "value": incident.mitigation[:1000],
                "inline": False,
            },
            {
                "name": "🔗 Source & Verification",
                "value": f"[Originalquelle]({incident.source_url})",
                "inline": False,
            },
        ]

        return {
            "title": f"{badge} #{index}/{total}: {incident.title[:200]}",
            "color": color,
            "fields": fields,
        }

    def build_payload_batches(self, data: CTIAnalysisResult) -> List[Dict[str, Any]]:
        """Smart chunker respecting Discord's max 10 embeds and 6,000 char limits."""
        batches: List[Dict[str, Any]] = []
        current_embeds: List[Dict[str, Any]] = []
        current_chars = 0

        # Always start with overview embed
        overview = self._build_overview_embed(data)
        current_embeds.append(overview)
        current_chars += len(overview.get("title", "")) + len(overview.get("description", ""))

        total_incidents = len(data.discord_report.incidents)
        for idx, inc in enumerate(data.discord_report.incidents, 1):
            embed = self._build_incident_embed(inc, idx, total_incidents)
            embed_chars = len(embed.get("title", "")) + sum(
                len(f.get("name", "")) + len(f.get("value", "")) for f in embed.get("fields", [])
            )

            # Check if adding this embed exceeds 10 embeds or 5,500 characters
            if len(current_embeds) >= 10 or (current_chars + embed_chars) > 5500:
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
            print("📢 [DRY-RUN] DISCORD WEBHOOK PAYLOAD PREVIEW")
            print("=" * 70)
            print(f"Total Batches / Messages: {len(batches)}")
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
