"""LLM Threat Analysis Processor using Google GenAI SDK with structured Pydantic output."""

import json
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from src.core.config import Settings
from src.core.models import (
    CTIAnalysisResult,
    DiscordReport,
    IncidentItem,
    RawArticle,
    XPayload,
)

logger = logging.getLogger("nullday.processor")


SYSTEM_PROMPT_TEMPLATE = """You are "NullDay Intel", an elite Cyber Threat Intelligence (CTI) analyst engine designed for senior security operations center (SOC) analysts, incident responders, and CISOs.

Analyze the provided raw security feed items collected during the '{mode}' observation window and synthesize an executive threat briefing.

CRITICAL REQUIREMENTS:
1. Prioritization Hierarchy:
   - Actively exploited in the wild (CISA KEV / 0-day) > Critical CVE (CVSS >= 8.0) > High-impact ransomware / extortion > Major verified data breach.
   - Discard low-impact noise, minor patch releases, or marketing fluff.

2. Discord Executive Report:
   - Provide a professional, concise executive summary paragraph (3-5 sentences) assessing the macro threat posture for the period.
   - For each prioritized incident, extract:
     * title: Clear, impact-focused incident headline
     * impact_sector: Affected sector or technology stack (e.g. Healthcare, Critical Infrastructure, Enterprise VPNs, Cloud Identity)
     * estimated_damage: Specific ransom demand / extortion amount / breach scope if disclosed, OR EXACTLY "Schadenssumme: Unbekannt / Nicht publiziert"
     * cvss: Float score (e.g. 9.8) if mentioned, else null
     * cve_id: Primary CVE (e.g. "CVE-2026-1234") or null
     * kev_status: true if listed in CISA KEV or confirmed active in-the-wild exploitation
     * mitigation: Concrete, actionable mitigation / remediation steps for defenders
     * source_url: Direct original reference link from the input articles

3. X (Twitter) Alert Payload:
   - tweet_text: MUST be strictly under 260 characters (leaving room for Twitter metadata / t.co shortlinks).
     * Focus on the single most critical threat or CVE of the batch.
     * Include affected target / sector.
     * End with 2-3 hashtags: #ThreatIntel #CyberSecurity #CVE (or #Ransomware).
   - thread_reply: A follow-up reply tweet strictly under 280 characters detailing concrete mitigation guidance and the primary source link.

4. Output Language:
   - The analysis and technical details should be in clear, professional English.
   - If damage is unstated, use the exact German standard string: "Schadenssumme: Unbekannt / Nicht publiziert".
"""


class CTIProcessor:
    """Processes raw security feed entries with Gemini into structured dual-publishing payloads."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or Settings.GEMINI_API_KEY
        self.model_name = model_name or Settings.GEMINI_MODEL

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No GEMINI_API_KEY provided. LLM processor running in mock/fallback mode.")

    def _build_context(self, articles: List[RawArticle]) -> str:
        """Format raw articles into concise context for the LLM."""
        if not articles:
            return "No new security incidents or CVE disclosures were collected during this observation window."

        lines = []
        for i, art in enumerate(articles[:25], 1):  # Cap at top 25 to respect prompt token economy
            cve_str = f" [CVEs: {', '.join(art.cve_candidates)}]" if art.cve_candidates else ""
            kev_flag = " [CRITICAL: ACTIVE KEV]" if art.is_kev else ""
            lines.append(
                f"### Entry {i}: {art.title}{cve_str}{kev_flag}\n"
                f"- Source: {art.source_name} | Published: {art.published_at.isoformat()}\n"
                f"- Link: {art.url}\n"
                f"- Summary: {art.summary.strip()[:400]}\n"
            )
        return "\n".join(lines)

    def _generate_mock_result(self, articles: List[RawArticle], mode: str) -> CTIAnalysisResult:
        """Generate a realistic fallback briefing when running offline or in mock test mode."""
        if not articles:
            return CTIAnalysisResult(
                discord_report=DiscordReport(
                    title=f"NullDay Intel // {mode.capitalize()} Briefing - Routine Status",
                    summary=f"No high-severity vulnerabilities or active exploitation campaigns exceeded threshold during this {mode} window. Perimeter hygiene and logging telemetry remain stable.",
                    threat_level="ROUTINE",
                    incidents=[],
                ),
                x_payload=XPayload(
                    tweet_text=f"🟢 NullDay Intel {mode.capitalize()} Update: Threat landscape stable across monitored feeds. No critical 0-days detected in the last cycle. #ThreatIntel #CyberSecurity",
                    thread_reply="Defenders: Routine audit of external attack surfaces and patch verification recommended. Full briefing in Discord.",
                ),
            )

        # Select highest-priority candidate (KEV or explicit CVE)
        candidates = [a for a in articles if a.is_kev or a.cve_candidates]
        top = candidates[0] if candidates else articles[0]
        cve = top.cve_candidates[0] if top.cve_candidates else "CVE-2026-UNSPECIFIED"
        mock_incidents = [
            IncidentItem(
                title=top.title,
                cve_id=cve if cve != "CVE-2026-UNSPECIFIED" else None,
                cvss=9.1 if top.is_kev else 8.4,
                kev_status=top.is_kev,
                impact_sector="Enterprise Infrastructure / Network Perimeter",
                estimated_damage="Schadenssumme: Unbekannt / Nicht publiziert",
                mitigation="Isolate exposed management interfaces, verify IOCs, and deploy latest vendor security update immediately.",
                source_url=top.url,
            )
        ]

        headline_tweet = f"🚨 ALERT: Critical exploit activity detected in {cve if cve != 'CVE-2026-UNSPECIFIED' else top.title[:40]}. Active perimeter threat. #ThreatIntel #CyberSecurity #CVE"
        if len(headline_tweet) > 260:
            headline_tweet = headline_tweet[:257] + "..."

        return CTIAnalysisResult(
            discord_report=DiscordReport(
                title=f"NullDay Intel // {mode.capitalize()} Cyber Threat Briefing",
                summary=f"Analysis of {len(articles)} ingested intelligence items indicates active threat vector targeting perimeter infrastructure. Immediate patch validation advised.",
                threat_level="CRITICAL" if any(a.is_kev for a in articles) else "HIGH",
                incidents=mock_incidents,
            ),
            x_payload=XPayload(
                tweet_text=headline_tweet,
                thread_reply=f"Mitigation: Restrict inbound access and patch per vendor advisory. Ref: {top.url[:80]}",
            ),
        )

    def process(self, articles: List[RawArticle], mode: str = "daily") -> CTIAnalysisResult:
        """Run LLM inference on raw articles to produce structured CTI briefings."""
        if not self.client:
            logger.info("Using mock/fallback CTI generator (no API key configured).")
            return self._generate_mock_result(articles, mode)

        if not articles:
            logger.info("No articles to analyze. Generating all-clear report.")
            return self._generate_mock_result([], mode)

        prompt_context = self._build_context(articles)
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(mode=mode)

        logger.info(
            f"Invoking Google GenAI model '{self.model_name}' for {len(articles)} articles (mode: {mode})..."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Raw Feed Articles:\n\n{prompt_context}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=CTIAnalysisResult,
                    temperature=0.2,  # Low temperature for analytical accuracy
                ),
            )

            # Retrieve parsed Pydantic model directly
            if hasattr(response, "parsed") and response.parsed:
                result: CTIAnalysisResult = response.parsed
            else:
                # Parse from text if needed
                raw_json = json.loads(response.text)
                result = CTIAnalysisResult.model_validate(raw_json)

            # Enforce strict character limits on Twitter output as defense-in-depth
            if len(result.x_payload.tweet_text) > 260:
                logger.warning(
                    f"LLM tweet text exceeded 260 chars ({len(result.x_payload.tweet_text)}). Truncating."
                )
                result.x_payload.tweet_text = result.x_payload.tweet_text[:257] + "..."

            if result.x_payload.thread_reply and len(result.x_payload.thread_reply) > 280:
                result.x_payload.thread_reply = result.x_payload.thread_reply[:277] + "..."

            logger.info("Successfully generated structured CTI briefing from GenAI.")
            return result

        except Exception as e:
            logger.error(f"GenAI processing failed: {e}. Falling back to deterministic briefing.", exc_info=True)
            print(f"\n⚠️ [NOTICE] GenAI API call returned: {e}. Falling back to rule-based briefing.")
            return self._generate_mock_result(articles, mode)
