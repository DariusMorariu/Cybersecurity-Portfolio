# Network & Security Architecture

This directory houses network diagrams, data flow models, and security boundary documentation for all lab infrastructure and projects.

---

## Lab Network Segmentation Design

The homelab utilizes **802.1Q VLAN trunking** configured on a TP-Link TL-SG108E managed switch paired with Proxmox VE's VLAN-aware Linux bridge (`vmbr0`).

| VLAN ID | Subnet / Segment | Purpose | Isolation & Security Policy |
| :---: | :--- | :--- | :--- |
| **VLAN 1** | Management & Home LAN | Proxmox VE Web GUI, SSH Management, Home LAN | Untagged switch traffic. Direct internet access for updates. |
| **VLAN 30** | Cyber Security Lab (`10.30.0.0/24`) | Target VMs (OWASP Juice Shop, vulnerable containers) | **Air-Gapped / Isolated:** No default gateway, no outbound Internet access, no DNS resolution. |
| **Dual-Homed** | Wazuh SIEM Interface (`10.30.0.100`) | Log Collector & Security Telemetry | Wazuh server has an interface in VLAN 1 (for updates/management) and an interface in VLAN 30 (`ens19`, no default gateway) to pull agent telemetry without routing traffic between segments. |

---

## Architecture Diagram Standards

To ensure clean and reproducible architecture artifacts:
- **Diagram Tooling:** Mermaid (`.mmd` or embedded in Markdown), draw.io (`.drawio`), or PlantUML.
- **Export Formats:** Include both editable source files and high-resolution SVG or PNG exports for presentation.
- **Security Boundary Annotations:** Always clearly delineate trust boundaries, firewall filters, and layer 2 vs. layer 3 separations.

---

## Sanitization Policy

All published architecture diagrams and schemas must strictly adhere to the following privacy rules:
- **RFC 1918 Private Addresses:** Use standard documentation ranges (`10.0.0.0/8`, `172.16.0.0/12`, or `192.168.0.0/16`) or RFC 5737 documentation subnets (`192.0.2.0/24`, `198.51.100.0/24`).
- **Identifiers:** Never expose public WAN IP addresses, internal ISP router credentials, MAC addresses, or production domain names.
