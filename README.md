# Cybersecurity Portfolio - Darius-Simon Morariu

Practical documentation of my cybersecurity learning path, homelab infrastructure, Hack The Box Academy labs, and defensive/offensive security projects.

I graduated from the HTL Donaustadt informatics department in 2026. My current focus is hands-on security engineering: networking, Linux system hardening, virtualization, SIEM telemetry, incident response, and penetration testing. I am actively working through the **HTB Academy Certified Junior Cybersecurity Analyst (CJCA)** and **Certified Penetration Testing Specialist (CPTS)** paths.

---

## Featured Project: Budget Cybersecurity Homelab

A custom-engineered, 3D-printed 10-inch homelab rack built around an upgraded Fujitsu ESPRIMO Q556/2 (32 GB RAM, 512 GB SSD) running Proxmox VE, an 8-port managed Gigabit switch with 802.1Q VLAN segmentation, dual-homed Wazuh SIEM monitoring, and an interactive ESP32 touch status display.

<p align="center">
  <img src="01_Homelab/images/homelab-final-front.png" alt="Custom 10-inch Cybersecurity Homelab" width="800">
</p>

👉 **[Explore the full Homelab Architecture, Hardware Validation & Build Log](01_Homelab/README.md)**

---

## Repository Structure

| Directory | Purpose |
| :--- | :--- |
| [📁 `01_Homelab`](01_Homelab/README.md) | Homelab architecture, 3D-print CAD, ESP32 wiring, hardware validation & build logs |
| [📁 `02_Lab_Reports`](02_Lab_Reports/README.md) | Sanitized offensive/defensive lab reports, vulnerability assessments & PoCs |
| [📁 `03_Incident_Reports`](03_Incident_Reports/README.md) | Incident response exercises, SOC alert triage, Wazuh telemetry & timeline analysis |
| [📁 `04_Projects`](04_Projects/README.md) | Standalone security software, tooling, and upcoming projects (*NullDay Intel*) |
| [📁 `05_Architecture`](05_Architecture/README.md) | Sanitized network topology diagrams, VLAN matrices & data flow schemas |
| [📁 `06_Scripts`](06_Scripts/README.md) | Security automation, audit scripts, API connectors & middleware utilities |
| [📁 `07_Evidence`](07_Evidence/README.md) | Sanitized screenshots, log artifacts, and proof-of-concept verification files |

---

## Core Skills & Tooling

- **Security & Systems:** Proxmox VE, Linux (Ubuntu/Debian) Administration & Hardening, Windows Administration, Docker
- **Networking & Defense:** 802.1Q VLAN Segmentation, Wazuh SIEM, Netplan, Wireshark, iptables, Syslog/auditd
- **Offensive Security & Labs:** Nmap, Burp Suite, Gobuster, SQL Injection, Privilege Escalation, OWASP Top 10, HTB Academy
- **Software Engineering:** Python, Bash, PowerShell, C# / Java / Dart, Node.js, SQL, Git & GitHub Actions
- **Hardware & IoT:** ESP32 SPI Touchscreen Integration, Microcontroller Firmware, 3D-Printing (OpenSCAD / Bambu Lab)

---

## Roadmap

- [x] Design, 3D-print, and assemble custom 10-inch homelab rack
- [x] Upgrade and benchmark Fujitsu host (32 GB RAM, thermal stress-testing)
- [x] Install and harden Proxmox VE hypervisor
- [x] Configure managed switch with 802.1Q VLANs (VLAN 1 Management, VLAN 30 Isolated Lab)
- [x] Deploy Wazuh SIEM manager in dual-homed configuration for secure log collection
- [x] Deploy air-gapped target VM (OWASP Juice Shop) with offline Wazuh Agent
- [x] Build and program ESP32 touch display with live Proxmox VE resource monitoring
- [ ] Deploy Windows Active Directory lab environment (Domain Controller & Windows 11 client)
- [ ] Document simulated attack and incident response workflows (IR-2026-001)
- [ ] Complete the HTB Academy CJCA (Certified Junior Cybersecurity Analyst) certification
- [ ] Proceed with HTB Academy CPTS (Certified Penetration Testing Specialist) track

---

## Ethics and Privacy Policy

All activities documented in this repository are conducted strictly in private, isolated lab environments or on explicitly authorized training platforms (e.g., Hack The Box).

In compliance with professional security standards:
- All screenshots, logs, network addresses, and configurations are sanitized and defanged prior to publication.
- No production credentials, private keys, API secrets, or personally identifiable information (PII) are ever committed.
- Unsanitized artifacts, PCAP captures, and local notes remain quarantined in `99_Private/` (enforced via `.gitignore`).

---

> *Work in progress: This portfolio is actively maintained and updated alongside ongoing homelab expansions, certifications, and security research.*
