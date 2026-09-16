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


SYSTEM_PROMPT_TEMPLATE = """You are "NullDay Intel", an elite Cyber Threat Intelligence (CTI) analyst engine designed for senior security operations center (SOC) analysts, incident response commanders, and CISOs.

Analyze the provided raw security feed items collected during the '{mode}' observation window and synthesize a comprehensive executive threat briefing.

ABSOLUTE STYLE & FORMATTING CONSTRAINTS:
1. ZERO EMOJIS: Do NOT use any emojis, icons, or decorative unicode symbols under any circumstances in any field (no shields, alerts, fire, warning signs, etc.). Maintain a strictly objective, authoritative, intelligence-grade tone aligned with CISA alerts, BSI Lageberichte, and Mandiant intelligence publications.
2. 5-MINUTE EXECUTIVE READ: This briefing must be thorough, analytical, and actionable. Avoid brief or superficial summaries. Provide in-depth technical analysis and context across all sections.

SECTION REQUIREMENTS:

1. Discord Executive Report:
   - summary: Detailed executive summary paragraph assessing the overall threat posture during this {mode} period.
   - strategic_analysis: Extensive multi-paragraph strategic assessment covering:
     * Threat Vector Trends: Perimeter vulnerabilities, identity provider exploitation, and supply-chain vectors.
     * Exploitation & KEV Activity: Analysis of actively exploited flaws and 0-day campaigns.
     * Ransomware & Threat Actor Syndicates: Active extortion campaigns, extortion methods, and target selection.
     * Strategic Defense Guidance: Priorities for hardening, patch management, and telemetry visibility.
   - key_recommendations: 3 to 5 prioritized strategic defensive directives for security leadership and engineering teams.
   - incidents: Thoroughly analyze and document between 4 and 8 prioritized incidents from the ingested articles:
     * title: Factual, professional headline without hype.
     * impact_sector: Affected sector and exact technology stack (e.g., Enterprise Perimeter VPNs, Healthcare Infrastructure, Cloud Identity Gateways).
     * estimated_damage: Disclosed extortion sums, fines, or data volumes; if undisclosed or unverified, write EXACTLY: "Schadenssumme: Unbekannt / Nicht publiziert".
     * cvss: Float score (e.g. 9.8) if mentioned, else null.
     * cve_id: Primary CVE (e.g. "CVE-2026-1234") or null.
     * kev_status: true if listed in CISA KEV or confirmed active in-the-wild exploitation.
     * mitigation: Concrete, actionable mitigation and patching instructions.
     * source_url: Direct original reference link from the input articles.

2. X (Twitter) Alert Payload:
   - tweet_text: Strictly under 260 characters without any emojis.
     * Factual and urgent tone starting with "[CTI ALERT]" or "[SECURITY ADVISORY]".
     * Highlight the #1 critical threat or CVE of the batch, the affected technology, and the immediate risk.
     * End with 2-3 hashtags: #ThreatIntel #CyberSecurity #CVE (or #Ransomware).
   - thread_reply: Strictly under 280 characters without any emojis. Concise mitigation steps and the primary reference link.

3. Prioritization Hierarchy:
   - Confirmed Active Exploitation (CISA KEV / 0-day) > Critical CVE (CVSS >= 8.0) > High-impact ransomware / extortion > Major verified data breach.
   - Discard low-impact marketing webinars, product pitches, or non-actionable fluff.
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
        for i, art in enumerate(articles[:35], 1):  # Feed top 35 to provide rich material for 5-min read
            cve_str = f" [CVEs: {', '.join(art.cve_candidates)}]" if art.cve_candidates else ""
            kev_flag = " [CRITICAL: ACTIVE KEV]" if art.is_kev else ""
            lines.append(
                f"### Entry {i}: {art.title}{cve_str}{kev_flag}\n"
                f"- Source: {art.source_name} | Published: {art.published_at.isoformat()}\n"
                f"- Link: {art.url}\n"
                f"- Summary: {art.summary.strip()[:450]}\n"
            )
        return "\n".join(lines)

    def _generate_mock_result(self, articles: List[RawArticle], mode: str) -> CTIAnalysisResult:
        """Generate an in-depth, emoji-free fallback briefing for offline tests or demo runs."""
        if not articles:
            return CTIAnalysisResult(
                discord_report=DiscordReport(
                    title=f"Cyber Threat Assessment - {mode.capitalize()} Surveillance Status",
                    summary=f"Surveillance across all monitored intelligence feeds confirms that no zero-day vulnerabilities or active exploitation campaigns exceeded critical thresholds during the {mode} monitoring cycle. Perimeter hygiene and logging telemetry remain stable across enterprise boundaries.",
                    strategic_analysis=(
                        "During this observation window, vulnerability ingestion and threat telemetry indicate baseline defensive stability. "
                        "Security teams should prioritize scheduled patch audits, identity access reviews, and verification of external perimeter exposures. "
                        "Threat actor activity continues to focus on opportunistic scanning of unpatched network edge devices and misconfigured cloud identities."
                    ),
                    threat_level="ROUTINE",
                    key_recommendations=[
                        "Verify that all external-facing services maintain current vendor patch baselines.",
                        "Enforce strict multi-factor authentication (MFA) and conditional access on administrative endpoints.",
                        "Audit SIEM telemetry to confirm unbroken ingestion from perimeter firewalls and VPN gateways.",
                    ],
                    incidents=[],
                ),
                x_payload=XPayload(
                    tweet_text=f"[CTI UPDATE] NullDay Intel {mode.capitalize()} Briefing: Threat landscape stable across monitored feeds. No critical 0-days detected in current cycle. #ThreatIntel #CyberSecurity",
                    thread_reply="Defenders: Routine audit of external attack surfaces and patch verification recommended. Full briefing available in Discord.",
                ),
            )

        # Prioritize items with KEV or CVE candidates
        candidates = [a for a in articles if a.is_kev or a.cve_candidates]
        if not candidates:
            candidates = articles

        # Build 4 prioritized incident briefs for an in-depth briefing
        mock_incidents: List[IncidentItem] = []
        for idx, art in enumerate(candidates[:4], 1):
            cve = art.cve_candidates[0] if art.cve_candidates else "CVE-PENDING"
            is_critical = art.is_kev or (idx == 1)
            mock_incidents.append(
                IncidentItem(
                    title=art.title,
                    cve_id=cve if cve != "CVE-PENDING" else None,
                    cvss=9.2 if is_critical else 7.8,
                    kev_status=art.is_kev,
                    impact_sector="Enterprise Infrastructure & Perimeter Gateways",
                    estimated_damage="Schadenssumme: Unbekannt / Nicht publiziert",
                    mitigation=(
                        "1. Restrict external network access to administrative interfaces immediately.\n"
                        "2. Review authentication and access logs for anomalous session tokens.\n"
                        "3. Apply official vendor security update per advisory guidance."
                    ),
                    source_url=art.url,
                )
            )

        top = mock_incidents[0]
        top_cve = top.cve_id if top.cve_id else top.title[:50]

        strategic_text = (
            f"Intelligence aggregated across {len(articles)} disclosures reveals heightened adversary interest in enterprise perimeter technologies. "
            "Threat actors are increasingly compressing the window between public vulnerability disclosure and automated exploitation, "
            "frequently targeting gateway devices, authentication protocols, and unpatched web services. "
            "\n\n"
            "SOC teams must account for opportunistic post-exploitation lateral movement following initial access. "
            "Credential dumping and session hijacking continue to serve as primary entry points for secondary ransomware deployment."
        )

        headline_tweet = f"[CTI ALERT] Active exploitation detected in {top_cve}. Immediate perimeter containment and patch validation advised. #ThreatIntel #CyberSecurity #CVE"
        if len(headline_tweet) > 260:
            headline_tweet = headline_tweet[:257] + "..."

        return CTIAnalysisResult(
            discord_report=DiscordReport(
                title=f"Executive Cyber Threat Briefing // {mode.capitalize()} Assessment",
                summary=(
                    f"Operational threat analysis of {len(articles)} telemetry items collected during this {mode} cycle highlights active exploitation "
                    f"and critical exposure in perimeter technologies. Security operations teams are advised to execute immediate containment and verification workflows."
                ),
                strategic_analysis=strategic_text,
                threat_level="CRITICAL" if any(a.is_kev for a in articles) else "HIGH",
                key_recommendations=[
                    "Conduct immediate exposure discovery for affected perimeter and gateway appliances.",
                    "Verify file integrity and authentication logs across all administrative ingress points.",
                    "Ensure backup immutability and test offline disaster recovery workflows.",
                    "Ingest verified indicators of compromise (IOCs) directly into endpoint and perimeter blocklists.",
                ],
                incidents=mock_incidents,
            ),
            x_payload=XPayload(
                tweet_text=headline_tweet,
                thread_reply=f"Mitigation: Restrict inbound access and patch per vendor advisory. Reference: {top.source_url[:90]}",
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

        candidate_models = [self.model_name]
        for fallback in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for current_model in candidate_models:
            logger.info(
                f"Invoking Google GenAI model '{current_model}' for {len(articles)} articles (mode: {mode})..."
            )
            try:
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=f"Raw Feed Articles:\n\n{prompt_context}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=CTIAnalysisResult,
                        temperature=0.2,
                    ),
                )

                if hasattr(response, "parsed") and response.parsed:
                    result: CTIAnalysisResult = response.parsed
                else:
                    raw_json = json.loads(response.text)
                    result = CTIAnalysisResult.model_validate(raw_json)

                # Enforce character limits on Twitter output
                if len(result.x_payload.tweet_text) > 260:
                    result.x_payload.tweet_text = result.x_payload.tweet_text[:257] + "..."

                if result.x_payload.thread_reply and len(result.x_payload.thread_reply) > 280:
                    result.x_payload.thread_reply = result.x_payload.thread_reply[:277] + "..."

                logger.info(f"Successfully generated structured CTI briefing with model '{current_model}'.")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"GenAI call with '{current_model}' failed: {e}")
                # Continue loop to try next model

        logger.error(f"All GenAI models failed. Last error: {last_error}", exc_info=True)
        print(f"\n[NOTICE] All GenAI model attempts failed ({last_error}). Using deterministic briefing.")
        return self._generate_mock_result(articles, mode)
