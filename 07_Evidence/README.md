# Evidence & Proof-of-Concept Artifacts

This directory stores sanitized evidence files, screenshots, log excerpts, and test artifacts supporting the writeups in `02_Lab_Reports` and `03_Incident_Reports`.

---

## Evidence Naming Conventions

To ensure traceability between reports and supporting artifacts, files in this directory must use the corresponding Report ID as a prefix:

```text
[REPORT-ID]_[EVIDENCE-TYPE]-[INDEX].[EXT]
```

### Examples
- `LAB-2026-001_POC-01.png`: Step 1 of SQL injection demonstration for Lab 1.
- `LAB-2026-001_POC-02.png`: Step 2 showing database user retrieval.
- `IR-2026-001_WAZUH-ALERT-01.png`: Screenshot of Wazuh SIEM dashboard triggering rule 5503.
- `IR-2026-001_LOG-EXCERPT.txt`: Sanitized web server error log showing brute-force attempts.

---

## Sanitization & Privacy Rules

All evidence placed here must be pre-sanitized:
- **Redaction:** Blur or mask session tokens, cookies, passwords, and private identifiers before committing images.
- **Defanging:** Defang sensitive URLs or malicious domains (e.g., `hxxp://example[.]com`).
- **Raw Data Quarantine:** Unsanitized PCAP files, raw credential dumps, or sensitive internal data must remain strictly in `99_Private/` (which is excluded via `.gitignore`).
