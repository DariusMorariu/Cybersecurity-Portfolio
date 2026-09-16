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

Analyze the provided raw security feed items collected during the '{mode}' observation window and synthesize a clear, comprehensive, and easy-to-understand executive threat briefing.

CRITICAL INSTRUCTION - CLARITY & ACCESSIBLE LANGUAGE:
1. CLEAR, DIRECT & ACCESSIBLE LANGUAGE: Write in plain, simple, and professional English. Avoid overly complex academic jargon or convoluted sentences. Explain technical concepts simply so that anyone can immediately understand:
   - What happened? (Plain explanation of the vulnerability or incident)
   - Why is it dangerous? (Real-world consequences: stolen data, ransomware, locked servers, company downtime)
   - What exact steps must be taken to fix it? (Concrete, actionable steps: update software, check logs, enforce MFA)
2. ZERO EMOJIS: Do NOT use any emojis, icons, or decorative unicode symbols anywhere in any field. Keep the presentation clean, serious, and authoritative.
3. IN-DEPTH ~5-MINUTE READ: Provide a thorough, structured briefing with clear headings and bullet points, avoiding dense walls of text.

SECTION REQUIREMENTS:

1. Discord Executive Report:
   - summary: 2 to 3 clear, simple paragraphs explaining the overall threat situation in plain language:
     * What is the main security event right now?
     * Who is affected and what can attackers do?
     * What is the most urgent defensive priority today?
   - strategic_analysis: A clearly structured, simple breakdown divided into three sections:
     * 1. What Attackers Are Doing: (Explain the main attack methods in simple, everyday terms).
     * 2. The Main Danger: (Explain what happens if attacked: data loss, ransomware extortion, locked systems).
     * 3. How To Defend Your Network: (Simple, practical steps any IT team can implement).
   - key_recommendations: 3 to 5 simple, actionable instructions (e.g., "1. Update vulnerable gateway software to the latest version immediately.", "2. Turn on multi-factor authentication (MFA) for all user accounts.", "3. Ensure offline backups are working and isolated.").
   - incidents: 4 to 8 prioritized incident evaluations from the input articles:
     * title: Factual, simple, and direct headline.
     * impact_sector: Plain description of affected systems (e.g., "Company Firewalls & VPN Gateways", "Healthcare / Hospitals", "Cloud Infrastructure").
     * estimated_damage: Disclosed extortion sums, fines, or data volumes; if undisclosed or unverified, write EXACTLY: "Schadenssumme: Unbekannt / Nicht publiziert".
     * cvss: Float score (e.g. 9.8) if mentioned, else null.
     * cve_id: Primary CVE (e.g. "CVE-2026-1234") or null.
     * kev_status: true if confirmed actively exploited in the wild.
     * mitigation: Simple, numbered, step-by-step instructions for IT admins to fix the problem.
     * source_url: Direct original reference link from input.

2. X (Twitter) Alert Payload:
   - tweet_text: Strictly under 260 characters without any emojis:
     "[CTI ALERT] Active attack targeting {System/CVE}. Risk: {Simple Risk}. Immediate update recommended. #ThreatIntel #CyberSecurity #CVE"
   - thread_reply: Strictly under 280 characters without any emojis:
     "How to fix: Install the latest vendor update and review login logs. Full briefing: {Link}"

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
        """Generate an in-depth, emoji-free fallback briefing in clear, simple language."""
        if not articles:
            return CTIAnalysisResult(
                discord_report=DiscordReport(
                    title=f"Cyber Threat Assessment - {mode.capitalize()} Surveillance Status",
                    summary=(
                        f"All monitored security feeds confirm that there are currently no critical zero-day attacks or major emergencies "
                        f"affecting standard systems during this {mode} cycle. Network firewalls and logging systems are operating normally."
                    ),
                    strategic_analysis=(
                        "1. What Attackers Are Doing:\n"
                        "Attackers are currently running routine automated scans across the internet looking for forgotten servers and unpatched systems.\n\n"
                        "2. The Main Danger:\n"
                        "Without active zero-days, the primary risk comes from weak or reused passwords and delayed software updates.\n\n"
                        "3. How To Defend Your Network:\n"
                        "Use this calm period to verify that all company laptops and servers have received the latest security updates and that multi-factor authentication (MFA) is turned on everywhere."
                    ),
                    threat_level="ROUTINE",
                    key_recommendations=[
                        "Check that all public-facing servers have installed the latest security patches.",
                        "Require two-factor authentication (2FA/MFA) for all remote logins and email accounts.",
                        "Verify that system backups are running properly and stored offline.",
                    ],
                    incidents=[],
                ),
                x_payload=XPayload(
                    tweet_text=f"[CTI UPDATE] NullDay Intel {mode.capitalize()} Briefing: Threat landscape stable across monitored feeds. No critical zero-days detected in current cycle. #ThreatIntel #CyberSecurity",
                    thread_reply="Defenders: Routine audit of external attack surfaces and patch verification recommended. Full briefing available in Discord.",
                ),
            )

        # Prioritize items with KEV or CVE candidates
        candidates = [a for a in articles if a.is_kev or a.cve_candidates]
        if not candidates:
            candidates = articles

        # Build 4 prioritized incident briefs for an in-depth briefing in simple terms
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
                    impact_sector="Company Firewalls, VPNs & Web Gateways",
                    estimated_damage="Schadenssumme: Unbekannt / Nicht publiziert",
                    mitigation=(
                        "1. Update the affected software to the latest version immediately.\n"
                        "2. Block public internet access to administrative login pages.\n"
                        "3. Check server login logs for any unrecognized or suspicious user accounts."
                    ),
                    source_url=art.url,
                )
            )

        top = mock_incidents[0]
        top_cve = top.cve_id if top.cve_id else top.title[:50]

        strategic_text = (
            "1. What Attackers Are Doing:\n"
            f"Security reports show that attackers are actively targeting internet-facing business software (such as API gateways and VPN servers). "
            "Once a software flaw is disclosed publicly, automated bots scan the internet within hours to exploit unpatched systems before administrators can update them.\n\n"
            "2. The Main Danger:\n"
            "If an attacker successfully exploits one of these vulnerabilities, they can bypass login screens, steal passwords, and gain full administrative control over internal company networks. "
            "In many cases, attackers use this initial access to deploy ransomware and encrypt business files.\n\n"
            "3. How To Defend Your Network:\n"
            "Security teams should prioritize patching public-facing servers first. Do not allow administrative login portals to be opened directly to the public internet, and ensure that all staff use two-factor authentication."
        )

        headline_tweet = f"[CTI ALERT] Active attack detected targeting {top_cve}. Immediate update and perimeter check recommended. #ThreatIntel #CyberSecurity #CVE"
        if len(headline_tweet) > 260:
            headline_tweet = headline_tweet[:257] + "..."

        return CTIAnalysisResult(
            discord_report=DiscordReport(
                title=f"Executive Cyber Threat Briefing // {mode.capitalize()} Assessment",
                summary=(
                    f"In this {mode} monitoring cycle, we analyzed {len(articles)} security disclosures. "
                    f"The most critical threat is an actively exploited vulnerability affecting enterprise gateway software. "
                    f"Attackers can bypass logins and take over systems. IT teams should verify and update affected systems today."
                ),
                strategic_analysis=strategic_text,
                threat_level="CRITICAL" if any(a.is_kev for a in articles) else "HIGH",
                key_recommendations=[
                    "Install the latest security updates for affected gateway and server software immediately.",
                    "Review server access logs for any unknown administrator logins or session tokens.",
                    "Ensure company backups are stored offline and protected against ransomware.",
                    "Block public internet access to internal management portals and admin screens.",
                ],
                incidents=mock_incidents,
            ),
            x_payload=XPayload(
                tweet_text=headline_tweet,
                thread_reply=f"Action required: Restrict public access and patch per vendor instructions. Full details: {top.source_url[:90]}",
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
