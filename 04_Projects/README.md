# Security Projects

This directory indexes independent cybersecurity software, security engineering systems, and tooling projects developed as part of my portfolio.

---

## Featured Projects

| Project | Domain | Description | Tech Stack | Status | Link |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Budget Cybersecurity Homelab** | Infrastructure & Defense | Custom 3D-printed 10-inch homelab rack, Proxmox virtualization, 802.1Q VLAN isolation, Wazuh SIEM telemetry, and ESP32 touch status monitor. | Proxmox VE, Wazuh SIEM, Linux, C++/Arduino, Docker, OpenSCAD | `Active` | [View Project](../01_Homelab/README.md) |
| **NullDay Intel** | Threat Intelligence | Serverless CTI briefing engine running via GitHub Actions: automated feed ingestion (CISA KEV, CERT-Bund), Google GenAI structured threat analysis, and dual-publishing to Discord & X/Twitter. | Python 3.11+, Google GenAI SDK, SQLite, Tweepy, GitHub Actions | `Active` | [View Project](NullDay%20Intel/README.md) |

---

## Project Structure Standard

Every standalone project in this folder follows a standard repository format:
1. **`README.md`**: Project overview, architecture diagram, threat model, setup guide, and usage examples.
2. **Source Code**: Clean, documented code adhering to security best practices (no hardcoded secrets, input sanitization).
3. **Tests & Demos**: Reproducible test cases or proof-of-concept demonstrations.
