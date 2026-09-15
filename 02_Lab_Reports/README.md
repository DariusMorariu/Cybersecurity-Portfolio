# Cybersecurity Lab Reports

This directory contains technical documentation and reports for hands-on cybersecurity labs, penetration testing practice, and security configuration experiments.

Labs documented here are performed either in my private isolated homelab environment (VLAN 30) or on authorized training platforms including **Hack The Box (HTB) Academy** and **PortSwigger Web Security Academy**.

---

## Purpose & Methodology

The objective of these reports is to demonstrate:
- **Offensive Security Competencies:** Practical enumeration, vulnerability exploitation, privilege escalation, and lateral movement techniques.
- **Defensive & Detection Understanding:** Correlating offensive actions with system artifacts, log generation, and SIEM alert triggers.
- **Remediation & Hardening:** Providing clear, actionable, developer- and administrator-friendly mitigation guidance.
- **Professional Communication:** Translating complex technical findings into structured executive summaries and technical details.

---

## Lab Reports Index

| Report ID | Title | Target / Platform | Category | Key Findings / Topics | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `LAB-2026-001` | [OWASP Juice Shop Vulnerability Assessment](LAB-2026-001_Juice_Shop.md) | Local Homelab (VLAN 30) | Web App Security | SQL Injection, Broken Authentication, Sensitive Data Exposure | `In Progress` |
| `LAB-2026-002` | Linux Host Hardening & Privilege Escalation | Local Homelab (Ubuntu Server) | System Hardening | SUID binaries, misconfigured sudoers, systemd service security | `Planned` |
| `LAB-2026-003` | Active Directory Enumeration & Kerberoasting | Homelab AD Lab (Windows Server) | Active Directory | LDAP queries, Kerberos ticket extraction, SPN analysis | `Planned` |
| `LAB-2026-004` | Network Enumeration & Service Discovery | Dedicated Test Subnet | Network Security | Nmap NSE scripts, banner grabbing, service fingerprinting | `Planned` |

---

## Standard Lab Report Template

All lab reports in this repository adhere to a standardized, professional structure:

```markdown
# [LAB-ID] Target / Lab Title

**Date:** YYYY-MM-DD  
**Author:** Darius-Simon Morariu  
**Category:** Web Application / Network / System Hardening / Active Directory  
**Target Environment:** Isolated Lab (VLAN 30) / HTB Academy  

---

## 1. Executive Summary
Brief high-level overview of the exercise, objectives, findings, and overall risk posture.

## 2. Scope & Target Environment
- **Target OS / Platform:** e.g., Ubuntu 24.04 LTS / Windows Server 2022
- **Network Scope:** e.g., Isolated VLAN 30 (`10.30.0.0/24`)
- **Authorized Tools Used:** e.g., Nmap, Burp Suite Community, Curl, Gobuster

## 3. Technical Walkthrough & Proof of Concept (PoC)
### 3.1 Reconnaissance & Enumeration
- Findings from initial port scanning, directory fuzzing, and service analysis.
- Relevant command outputs and sanitized screenshot references.

### 3.2 Vulnerability Analysis & Exploitation
- Root cause explanation of the identified vulnerability (e.g., lack of input parameterization).
- Step-by-step reproducible exploit demonstration.
- Severity classification: **Critical / High / Medium / Low / Informational** (CVSS v3.1).

## 4. Remediation & Hardening Guidance
- Concrete code fixes, configuration changes, or policy adjustments required to mitigate the vulnerability.
- Defensive configuration snippets (e.g., input sanitization, least privilege, firewall rules).

## 5. Detection & Log Telemetry
- How this attack appears in log files (`/var/log/auth.log`, web server access logs, Windows Event Logs).
- Wazuh SIEM rule or Sigma rule pattern to detect similar activity in real time.
```

---

## Rules of Engagement & Ethics

- **Authorization:** All tests are conducted strictly against self-hosted virtual machines or explicitly approved training targets.
- **Data Protection:** No proprietary company data, real personal identifiable information (PII), or production infrastructure credentials appear in any report.
- **Sanitization:** Network addresses, hostnames, and cryptographic hashes are defanged or randomized where appropriate.