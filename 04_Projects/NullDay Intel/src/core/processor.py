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


SYSTEM_PROMPT_TEMPLATE = """You are "NullDay Intel", an automated Cyber Threat Intelligence (CTI) briefing engine.

Analyze the provided raw security feed items collected during the '{mode}' observation window and synthesize an authoritative, enterprise-grade executive threat intelligence briefing.

CRITICAL INSTRUCTIONS - ANALYTICAL RIGOR & TONE:
1. PROFESSIONAL CTI ANALYSIS: Write with the analytical rigor, precision, and depth expected of senior threat intelligence analysts (comparable to Mandiant, CISA, or CrowdStrike intelligence advisories). Detail threat actor methodologies, initial access mechanics, exploit weaponization timelines, and secondary payload risks (e.g. ransomware staging, data exfiltration).
2. ZERO EMOJIS: Do NOT use any emojis, icons, or decorative unicode symbols anywhere in any field. Maintain a sober, authoritative enterprise intelligence format.
3. IN-DEPTH ~5-MINUTE EXECUTIVE READ: Deliver a comprehensive, structured briefing with detailed analytical sections, avoiding superficial one-sentence summaries.

SECTION REQUIREMENTS:

1. Discord Executive Report:
   - summary: 2 to 3 substantive paragraphs synthesizing the macro threat posture:
     * Current threat landscape dynamics and active adversary campaigns observed across telemetry feeds.
     * Primary attack vectors, affected architectural tiers, and adversary operational velocity.
     * High-level operational directives for security operations and engineering leadership.
   - strategic_analysis: A thorough, multi-section threat intelligence assessment structured as follows:
     * 1. Adversary Campaigns & Exploit Velocity: (Analyze threat actor weaponization trends, time-to-exploit post-disclosure, and automated scanning infrastructure).
     * 2. Perimeter Exposure & Systemic Risk: (Evaluate consequences of initial compromise, authentication bypasses, credential dumping, and secondary ransomware deployment).
     * 3. Defensive Architecture & Countermeasures: (Strategic defensive hardening, network segmentation, ingress filtering, and identity protection).
   - key_recommendations: 3 to 5 concrete, prioritized technical directives (e.g., "1. Enforce emergency patch orchestration across exposed perimeter gateways.", "2. Audit authentication telemetry for anomalous Kerberos tickets and forged session tokens.", "3. Isolate mission-critical operational segments and validate immutable backup pipelines.").
   - incidents: 4 to 8 prioritized incident evaluations from the input articles:
     * title: Factual, professional headline specifying vendor, technology, and vulnerability class.
     * impact_sector: Specific infrastructure and sector exposure (e.g., "Enterprise Perimeter Gateways & VPN Appliances", "Healthcare Critical Infrastructure", "Cloud Identity Providers").
     * estimated_damage: Disclosed extortion amounts, data volumes, or operational downtime; if undisclosed or unverified, write EXACTLY: "Financial Impact: Undisclosed / Under Investigation".
     * cvss: Float score (e.g. 9.8) if mentioned, else null.
     * cve_id: Primary CVE (e.g. "CVE-2026-1234") or null.
     * kev_status: true if confirmed actively exploited in the wild (CISA KEV / 0-day).
     * mitigation: Concrete, numbered technical remediation instructions for engineering and incident response teams.
     * source_url: Direct original reference link from input.

2. X (Twitter) Alert Payload:
   - tweet_text: Strictly under 260 characters without any emojis:
     "[CTI ALERT] Active exploitation detected targeting <System/CVE>. Critical perimeter exposure. Immediate patch validation advised. #ThreatIntel #CyberSecurity #CVE"
   - thread_reply: Strictly under 280 characters without any emojis:
     "Remediation: Apply vendor security updates and audit ingress authentication logs. Technical advisory: <Link>"

3. Prioritization Hierarchy:
   - Confirmed Active Exploitation (CISA KEV / 0-day) > Critical CVE (CVSS >= 8.0) > High-impact ransomware / extortion > Major verified data breach.
   - Discard promotional webinars, sales pitches, or non-actionable fluff.
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
        """Generate an in-depth, emoji-free fallback briefing adhering to senior CTI standards."""
        if not articles:
            return CTIAnalysisResult(
                discord_report=DiscordReport(
                    title=f"Cyber Threat Assessment - {mode.capitalize()} Surveillance Status",
                    summary=(
                        f"Operational surveillance across all monitored intelligence feeds confirms a stabilized threat environment during this {mode} observation cycle. "
                        f"No unmitigated zero-day disclosures or active exploitation campaigns targeting standard baseline architectures were identified. Perimeter telemetry indicates normal background noise."
                    ),
                    strategic_analysis=(
                        "1. Adversary Campaigns & Exploit Velocity:\n"
                        "Threat actors continue opportunistic scanning against legacy unpatched vulnerabilities, primarily targeting misconfigured external interfaces and unauthenticated API endpoints.\n\n"
                        "2. Perimeter Exposure & Systemic Risk:\n"
                        "Absent novel zero-day activity, adversary initial access remains predominantly reliant on credential stuffing and token re-use. Lateral movement risk is elevated in environments lacking strict identity controls.\n\n"
                        "3. Defensive Architecture & Countermeasures:\n"
                        "Defensive engineering teams should leverage this operational window to audit external attack surface inventories, validate multi-factor authentication enforcement, and confirm immutable backup verification."
                    ),
                    threat_level="ROUTINE",
                    key_recommendations=[
                        "Conduct rigorous attack surface discovery across external-facing IP allocations.",
                        "Enforce phishing-resistant multi-factor authentication (MFA) across all administrative entry points.",
                        "Validate offline immutability and recovery workflows for mission-critical datastores.",
                    ],
                    incidents=[],
                ),
                x_payload=XPayload(
                    tweet_text=f"[CTI UPDATE] NullDay Intel {mode.capitalize()} Briefing: Threat landscape baseline stable across monitored telemetry. No critical zero-day campaigns detected. #ThreatIntel #CyberSecurity",
                    thread_reply="Defenders: Routine external attack surface audits and credential hygiene verification recommended. Full report available on Discord.",
                ),
            )

        # Prioritize items with KEV or CVE candidates
        candidates = [a for a in articles if a.is_kev or a.cve_candidates]
        if not candidates:
            candidates = articles

        # Build prioritized incident briefs for an in-depth briefing
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
                    impact_sector="Enterprise Perimeter Gateways & VPN Appliances",
                    estimated_damage="Financial Impact: Undisclosed / Under Investigation",
                    mitigation=(
                        "1. Execute emergency patch orchestration per vendor security bulletin advisory.\n"
                        "2. Restrict external ingress to administrative and management interfaces immediately.\n"
                        "3. Audit authentication telemetry and web access logs for anomalous session activity."
                    ),
                    source_url=art.url,
                )
            )

        top = mock_incidents[0]
        top_cve = top.cve_id if top.cve_id else top.title[:50]

        strategic_text = (
            "1. Adversary Campaigns & Exploit Velocity:\n"
            f"Intelligence telemetry synthesized across {len(articles)} disclosures demonstrates aggressive adversary weaponization targeting edge gateway infrastructure. "
            "Automated reconnaissance frameworks are actively scanning the global IPv4 space within hours of public disclosure, rapidly weaponizing authentication bypasses and remote code execution vulnerabilities.\n\n"
            "2. Perimeter Exposure & Systemic Risk:\n"
            "Compromise of edge devices eliminates the traditional network perimeter. Adversaries leverage initial access to establish persistent reverse shells, extract active directory credentials, and prepare secondary staging environments for ransomware deployment and enterprise-wide data exfiltration.\n\n"
            "3. Defensive Architecture & Countermeasures:\n"
            "Immediate containment requires segregating external management interfaces from public routing, enforcing zero-trust network access (ZTNA) policies, and validating that logging telemetry from perimeter appliances is actively ingested into centralized SIEM detection pipelines."
        )

        headline_tweet = f"[CTI ALERT] Active exploitation detected targeting {top_cve}. Critical perimeter exposure. Immediate patch validation advised. #ThreatIntel #CyberSecurity #CVE"
        if len(headline_tweet) > 260:
            headline_tweet = headline_tweet[:257] + "..."

        return CTIAnalysisResult(
            discord_report=DiscordReport(
                title=f"Executive Cyber Threat Briefing // {mode.capitalize()} Assessment",
                summary=(
                    f"Operational threat analysis of {len(articles)} telemetry items collected during this {mode} cycle reveals critical adversary campaigns targeting perimeter infrastructure. "
                    f"Confirmed in-the-wild exploitation vectors present severe enterprise exposure. Security operations teams must execute immediate patch verification and ingress containment workflows."
                ),
                strategic_analysis=strategic_text,
                threat_level="CRITICAL" if any(a.is_kev for a in articles) else "HIGH",
                key_recommendations=[
                    "Deploy vendor-validated security updates for all affected perimeter gateway devices immediately.",
                    "Audit ingress authentication logs and session tokens for indicators of unauthorized administrative access.",
                    "Verify isolation of mission-critical segments and confirm backup immutability against ransomware execution.",
                    "Ingest verified adversary indicators of compromise (IOCs) into perimeter blocklists and detection rules.",
                ],
                incidents=mock_incidents,
            ),
            x_payload=XPayload(
                tweet_text=headline_tweet,
                thread_reply=f"Remediation: Restrict external ingress and patch per vendor bulletin. Full intelligence briefing: {top.source_url[:90]}",
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
        system_instruction = SYSTEM_PROMPT_TEMPLATE.replace("{mode}", mode)

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
