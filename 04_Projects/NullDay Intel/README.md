# NullDay Intel ⚡
### Serverless Cyber Threat Intelligence (CTI) Briefing & Dual-Publishing Engine

[![CI Pipeline](https://github.com/DariusMorariu/Cybersecurity-Portfolio/actions/workflows/pipeline.yml/badge.svg)](https://github.com/DariusMorariu/Cybersecurity-Portfolio/actions/workflows/pipeline.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20GenAI-Gemini%202.5-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**NullDay Intel** is an enterprise-grade, serverless Cyber Threat Intelligence (CTI) engine designed for SOC analysts, incident responders, and security engineers. 

Operating autonomously via **GitHub Actions**, it continuously ingests high-value threat feeds (including CISA KEV, CERT-Bund, ENISA, and leading security newsrooms), analyzes and prioritizes incidents using the **Google GenAI SDK (`gemini-2.5-flash`)** with strict **Pydantic structured output**, and dual-publishes actionable briefings to **Discord** (deep-dive executive rich embeds) and **X / Twitter** (high-impact alert threads).

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Sched["1. Automation & Scheduling"]
        GH_Cron["GitHub Actions Cron<br/>• 08:00 CEST (06:00 UTC)<br/>• 18:00 CEST (16:00 UTC)<br/>• Weekly Sun 18:00 UTC<br/>• Monthly 1st 08:00 UTC"]
        Dispatch["Workflow Dispatch<br/>(Manual Trigger / Test)"]
    end

    subgraph Ingest["2. CTI Ingestion Engine"]
        CISA["CISA KEV (JSON Catalog)"]
        CERT["CERT-Bund (RSS)"]
        ENISA["ENISA Advisories (RSS)"]
        News["BleepingComputer / THN / Krebs (RSS)"]
        Agg["Feed Aggregator & Time-Window Filter"]
    end

    subgraph State["3. Deduplication & Persistence"]
        DB[(SQLite DB<br/>intel_history.db)]
        Dedup{"Deduplication<br/>Filter"}
    end

    subgraph LLM["4. AI Threat Analysis Engine"]
        Gemini["Google GenAI SDK<br/>(gemini-2.5-flash)"]
        Schema["Pydantic Structured Output<br/>CTIAnalysisResult"]
    end

    subgraph Pub["5. Multi-Publisher Engine"]
        Discord["Discord Webhook Publisher<br/>• Smart Chunker (4096 char / 10 embeds)<br/>• Severity Color-Coding (Red / Orange / Blue)<br/>• Damage & Mitigation Badges"]
        X["X / Twitter Publisher (API v2)<br/>• Character Guard (< 260 chars)<br/>• Thread Chaining (Root + Reply)"]
    end

    GH_Cron --> Agg
    Dispatch --> Agg
    CISA --> Agg
    CERT --> Agg
    ENISA --> Agg
    News --> Agg

    Agg --> Dedup
    DB <-->|Check Prior Hashes| Dedup
    Dedup -->|Unseen Incidents| Gemini
    Gemini --> Schema
    Schema --> Discord
    Schema --> X
    Pub -->|Update State [skip ci]| DB
```

---

## ✨ Key Features

### 1. Dual-Publishing Engine
- **Discord Executive Briefing:**
  - Designed for a ~5-minute executive read.
  - Multi-embed formatting with automated chunking (adheres to Discord's 4,096-character embed limit, 10-embed message cap, and 6,000-character payload ceiling).
  - Dynamic severity color-coding:
    - 🔴 **Critical Red (`#ED4245`):** Active CISA KEV exploitation, 0-days, or CVSS >= 9.0.
    - 🟠 **High Orange (`#E67E22`):** Ransomware campaigns, extortion events, and high-impact vulnerabilities.
    - 🔵 **Dark Blue (`#34495E`):** Weekly & monthly macro threat digests.
  - Every incident includes impact sector, damage estimation (`Schadenssumme: Unbekannt / Nicht publiziert`), concrete mitigation steps, and a clickable `[Originalquelle](URL)` link.
- **X (Twitter) Urgent Alert:**
  - Root tweet strictly formatted under 260 characters (leaving space for Twitter links and metadata).
  - Highlights the single most critical threat/CVE of the batch, the affected sector, and targeted hashtags (`#ThreatIntel #CyberSecurity #CVE`).
  - Automated thread continuation (`in_reply_to_tweet_id`) delivering defensive mitigations and reference links.

### 2. Execution Modes & Scheduling
Orchestrated via `.github/workflows/pipeline.yml`:
- **Daily (Twice Daily):**
  - Runs daily at **08:00 CEST (06:00 UTC)** and **18:00 CEST (16:00 UTC)**.
  - Filter: Last 24–26 hours focusing on active exploitation (KEV), critical CVEs (CVSS >= 8.0), ransomware attacks, and verified data breaches.
- **Weekly:**
  - Runs **Sundays at 18:00 UTC**.
  - Filter: Past 7 days macro review (top exploited flaws, sector impact, campaign patterns).
- **Monthly:**
  - Runs on the **1st of each month at 08:00 UTC**.
  - High-level strategic threat review and emerging threat-actor trends.

### 3. Serverless State & Deduplication
- Local SQLite database (`data/intel_history.db`) indexes article hashes (SHA-256 of canonical URLs), CVE identifiers, and run history.
- The GitHub Actions workflow automatically commits and pushes state changes back to the repository using `[skip ci]`, guaranteeing that no incident is ever published twice.

### 4. Curated CTI Sources (`config/sources.yaml`)
- **CISA KEV Catalog:** Official US Cybersecurity and Infrastructure Security Agency Known Exploited Vulnerabilities JSON feed.
- **CERT-Bund WID:** Federal Office for Information Security (BSI) Germany vulnerability advisories.
- **ENISA:** European Union Agency for Cybersecurity threat reports.
- **BleepingComputer:** Breaking security breaches and ransomware tracking.
- **The Hacker News:** Vulnerability intelligence and threat-actor campaigns.
- **Krebs on Security:** Deep investigative reporting on cybercrime syndicates.
- **Dark Reading:** Enterprise security posture and incident reporting.

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- Python 3.11 or newer
- Git

### 2. Installation
```bash
# Clone repository
git clone https://github.com/DariusMorariu/Cybersecurity-Portfolio.git
cd Cybersecurity-Portfolio/04_Projects/NullDay\ Intel

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the template and configure your API credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Google Gemini API
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/.../...

# X / Twitter API v2 (OAuth 1.0a User Context)
X_CONSUMER_KEY=...
X_CONSUMER_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

---

## 💻 CLI Usage

NullDay Intel includes a feature-rich CLI with full `--dry-run` simulation:

```bash
# Run daily briefing in dry-run mode (prints Discord & X payloads to stdout)
python main.py --mode daily --dry-run

# Force re-evaluation of all feed items (ignoring SQLite cache)
python main.py --mode daily --dry-run --force

# Run weekly digest
python main.py --mode weekly --dry-run

# Live execution (publishes to configured Discord webhook & X account)
python main.py --mode daily
```

### Dry-Run Output Preview

```text
======================================================================
📢 [DRY-RUN] DISCORD WEBHOOK PAYLOAD PREVIEW
======================================================================
Total Batches / Messages: 1

--- Batch 1/1 (2 embeds) ---

[Embed 1] Title: 🛡️ NullDay Intel // Daily Cyber Threat Briefing
Description:
**Posture Assessment:** 🔴 CRITICAL THREAT

Analysis indicates active in-the-wild exploitation targeting enterprise boundary appliances.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • 📊 Monitored Incidents: 1 threats analyzed in this cycle
  • 🚨 KEV Alerts: 1 active 0-day / in-the-wild exploits

[Embed 2] Title: 🚨 [ACTIVE EXPLOIT / KEV] #1/1: Cisco ASA/FTD Authentication Bypass
  • 🎯 Target / Impact Sector: Enterprise VPN & Firewall Perimeter
  • ⚡ Severity & Identifier: `CVE-2026-1234` • CVSS 9.8
  • 💰 Estimated Impact / Damage: Schadenssumme: Unbekannt / Nicht publiziert
  • 🛡️ Defensive Action & Mitigation: Apply vendor patch immediately. Restrict admin web interfaces.
  • 🔗 Source & Verification: [Originalquelle](https://nvd.nist.gov/vuln/detail/CVE-2026-1234)
======================================================================

======================================================================
🐦 [DRY-RUN] X / TWITTER ALERT PREVIEW
======================================================================
Root Tweet (174 / 280 chars):
>>> 🚨 ALERT: Active in-the-wild exploitation of Cisco ASA/FTD (CVE-2026-1234, CVSS 9.8). Immediate perimeter patching required. #ThreatIntel #CyberSecurity #CVE

Thread Reply (122 / 280 chars):
>>> Defensive Action: Restrict admin ports and apply latest vendor patch release. Ref: https://nvd.nist.gov/vuln/detail/CVE-2026-1234
======================================================================
```

---

## 🧪 Testing

Run the automated test suite covering feed parsing, SQLite deduplication, Discord chunking, X length validation, and CLI dry-run execution:

```bash
python -m pytest tests/ -v
```

---

## 🔐 GitHub Actions Secrets Setup

To run NullDay Intel automatically via GitHub Actions:

1. Navigate to your repository on GitHub: **Settings > Secrets and variables > Actions**.
2. Add the following repository secrets:

| Secret Name | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API Key for Gemini |
| `DISCORD_WEBHOOK_URL` | Webhook URL for the Discord channel |
| `X_CONSUMER_KEY` | X Developer App Consumer Key (API Key) |
| `X_CONSUMER_SECRET` | X Developer App Consumer Secret (API Key Secret) |
| `X_ACCESS_TOKEN` | X Developer Access Token (Read and Write) |
| `X_ACCESS_TOKEN_SECRET`| X Developer Access Token Secret |

---

## 📂 Project Structure

```text
04_Projects/NullDay Intel/
├── config/
│   └── sources.yaml            # Curated CTI feed URLs & configurations
├── data/
│   ├── .gitkeep                # Git tracking for persistence directory
│   └── intel_history.db        # SQLite persistence database (created at runtime)
├── src/
│   ├── core/
│   │   ├── config.py           # Environment variables, logging, modes
│   │   ├── models.py           # Pydantic schemas (IncidentItem, DiscordReport, XPayload)
│   │   └── processor.py        # google-genai LLM processor with structured output
│   ├── ingestion/
│   │   ├── base.py             # Feed fetcher abstract base & CVE extraction
│   │   ├── rss.py              # RSS/Atom parser with publication time window filter
│   │   ├── cisa_kev.py         # CISA KEV JSON catalog ingestor
│   │   └── aggregator.py       # Source aggregator & orchestrator
│   ├── storage/
│   │   └── database.py         # SQLite persistence & deduplication engine
│   └── publishers/
│       ├── base.py             # BasePublisher abstract interface
│       ├── discord.py          # Discord webhook with smart embed chunking & color-coding
│       └── x_twitter.py        # X API v2 thread publisher via tweepy
├── tests/
│   ├── test_aggregator.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_discord.py
│   ├── test_ingestion.py
│   ├── test_processor.py
│   └── test_publishers.py
├── .env.example                # Environment variables template
├── main.py                     # CLI entrypoint (--mode, --dry-run, --force)
├── requirements.txt            # Production dependencies
└── README.md                   # Architecture & setup manual
```

---

## ⚖️ Ethics & Responsible Disclosure

NullDay Intel strictly reports on publicly disclosed vulnerabilities, government security advisories (CISA KEV, BSI), and verified open-source threat reporting. No proprietary data, active exploitation code, or private victim details are disseminated. All references link directly to original source documentation.
