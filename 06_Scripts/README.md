# Security & Automation Scripts

This directory contains standalone automation scripts, defensive telemetry collectors, and helper utilities used across the homelab and lab exercises.

---

## Development & Security Standards

Every script committed to this repository must follow strict security and code quality standards:

1. **No Hardcoded Secrets:** Passwords, API tokens, and SSH keys must be ingested exclusively via environment variables or local ignored config files (`.env`).
2. **Defensive Error Handling:** Scripts must handle network timeouts, missing dependencies, and edge cases gracefully with clear error logging.
3. **Safe Execution:** Scripts must not execute destructive actions without explicit user confirmation flags (e.g., `--force` or `--dry-run`).
4. **Header Documentation:** Each script must include a header explaining:
   - Purpose & Security Context
   - Prerequisites & Required Python packages (`requirements.txt`)
   - Example Usage & Expected Output
   - Known limitations

---

## Script Categories

| Category | Typical Languages | Use Cases |
| :--- | :--- | :--- |
| **Lab Automation** | Bash, Python | Setting up isolated VM environments, automated package deployment in air-gapped subnets. |
| **SIEM & Log Parsing** | Python | Querying Wazuh REST API, parsing auth logs, normalizing Sysmon events. |
| **Network Auditing** | Python, PowerShell | Subnet verification, ARP sweep validation, VLAN tag sanity checks. |
| **ESP32 & IoT Middleware** | Node.js, C++ | Interacting with Proxmox VE API to render real-time resource telemetry on SPI displays. |
