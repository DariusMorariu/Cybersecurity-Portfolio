# NullDay Intel

> **Status:** In Planning / Under Active Design 🚧

---

## Project Overview

**NullDay Intel** is an upcoming cybersecurity project designed to aggregate, parse, and analyze threat intelligence feeds, zero-day alerts, and known exploited vulnerabilities (KEV) from open-source feeds (such as CISA KEV, AlienVault OTX, and security RSS feeds).

### Planned Features

- **Automated Feed Ingestion:** Periodic fetching and normalization of threat intelligence indicators (IOCs, CVEs, suspicious hashes, and IP ranges).
- **Enrichment & Scoring:** Correlating extracted CVEs with CVSS scores, EPSS probability, and known active exploitation in the wild.
- **Alert Dispatcher:** Configurable notification hooks (e.g., Discord/Slack webhook, email, or Wazuh custom ruleset integration).
- **CLI & Web Dashboard:** Intuitive interface to query active indicators and recent threat actor campaigns.

---

## Tech Stack (Planned)

- **Language:** Python 3.11+
- **Data Ingestion & Processing:** `httpx`, `asyncio`, `pydantic`
- **Storage:** SQLite / PostgreSQL
- **Security:** Secret management via environment variables, strict schema validation, defensive error handling

---

*This project will be developed and committed following the initial portfolio baseline cleanup.*
