# Homelab-Logbuch

Dieses Logbuch wird während des Aufbaus laufend ergänzt. Aus den Einträgen
entsteht später die fertige Word-Dokumentation für das Portfolio.

## 12.08.2026 - SIEM-Deployment & Security Monitoring (Phase 2)

### Wazuh Server & Dual-Homed Netzwerk-Architektur
- Wazuh als zentrales Open-Source-SIEM zur Überwachung des Homelabs installiert.
- Um die strikte Isolation des Hacking-Labs (VLAN 30) aufrechtzuerhalten, wurde eine "Dual-Homed"-Architektur umgesetzt.
- Der Wazuh-VM wurde in Proxmox auf Layer-2-Ebene eine zweite virtuelle Netzwerkkarte (`ens19`) mit VLAN-Tag 30 zugewiesen.
- Diese zweite Netzwerkkarte wurde via Netplan mit der festen IP `10.30.0.100/24` konfiguriert – **bewusst ohne Default-Gateway**, um ein Routing ins Internet auf Layer-3-Ebene komplett auszuschließen.

### Agent Deployment: Isoliertes Hacking-Lab (Juice Shop)
- Da die verwundbare Juice-Shop-VM (`10.30.0.20`) aus Sicherheitsgründen keinen Internetzugang besitzt, war ein klassisches Online-Deployment des Agenten nicht möglich.
- **Lösung (Offline-Deployment / Air-Gapped):** Das `.deb`-Paket wurde über das internetfähige Interface des Wazuh-Servers heruntergeladen und per `scp` über das isolierte VLAN-30-Interface auf die Ziel-VM übertragen.
- Die Installation erfolgte lokal über `dpkg`, wobei die IP des Managers via Umgebungsvariablen (`WAZUH_MANAGER`) übergeben wurde. Der Agent kommuniziert nun erfolgreich über das isolierte Netz.

### Agent Deployment: Proxmox Hypervisor
- Den Wazuh-Agenten direkt auf dem Proxmox-Host installiert, um das Fundament des Homelabs (Logins, Änderungen an Systemdateien via File Integrity Monitoring) zu überwachen.
- Initiale Installationsprobleme (fehlender Systembenutzer `wazuh` beim Start des Dienstes) wurden behoben, indem das lokale `.deb`-Paket über `apt` statt rein über `dpkg` entpackt wurde, um alle Installations-Skripte sauber auszuführen.
- Der Hypervisor funkt nun erfolgreich als zweiter aktiver Agent über das normale Heimnetz (VLAN 1) an das SIEM.

### Nächste Schritte
- **Active Directory (Geplant):** Eine Windows Server Umgebung (Domain Controller) inkl. Windows-Client als Basis für spätere HTB-relevante AD-Angriffe aufbauen.
- Erste simulierte Angriffe (z. B. fehlerhafte Logins) vom dedizierten Kali-Laptop auf den Juice Shop starten, um die Alarmierung im SIEM-Dashboard zu validieren.
- Backup- und Wiederherstellungskonzept für die kritischen VMs testen.

---

## 11.08.2026 - Finaler Build, Proxmox & Hacking-Lab

### Hardware-Build & 3D-Druck
- 10-Zoll-Rack (inklusive Halterungen für den Fujitsu und den Switch) vollständig auf dem Bambu Lab A1 Mini gedruckt und final montiert.
- Arbeitsspeicher des Fujitsu erfolgreich auf 32 GB DDR4 SO-DIMM (Non-ECC) aufgerüstet (anfängliches Kompatibilitätsproblem mit ECC-RAM gelöst).
- TP-Link-Switch und 8-Port-Keystone-Patchpanel physisch in das Rack integriert und mit kurzen Patchkabeln sauber verkabelt.
- ESP32 samt 3,5-Zoll-ILI9488-Touchdisplay in die gedruckte Frontblende eingebaut und erfolgreich verdrahtet (SPI-Bus). **Das Display zeigt nun live Proxmox-Graphen (CPU, Netzwerk) an und VMs lassen sich per Touch steuern.**

### Software & Virtualisierung
- Proxmox VE als Typ-1-Hypervisor installiert und konfiguriert.
- LXC-Container (ID 100, `middleware-ui`) für das ESP32-Backend mit Node.js und PM2 aufgesetzt. Ressourcenverbrauch optimal bei ca. 75 MB RAM. **Die Proxmox-API-Anbindung für die interaktive Display-Steuerung ist vollständig umgesetzt.**
- Erste Ziel-VM (ID 101, `juice-shop`) mit Ubuntu Server 24.04 LTS erstellt und OWASP Juice Shop als Docker-Container deployt.

### Netzwerk & Security-Isolation
- 802.1Q VLAN-Trunking auf dem TP-Link TL-SG108E Switch aktiv eingerichtet.
- **VLAN 1:** Heimnetz und Proxmox-Management (Untagged).
- **VLAN 30 (Cyber-Lab):** Isoliertes Hacking-Netz (Port 3 Tagged, Port 4 Untagged für den dedizierten Angreifer-Laptop).
- Virtueller Proxmox-Switch (`vmbr0`) arbeitet "VLAN aware".
- **Netzwerk-Härtung:** Die Ubuntu-VM (Juice Shop) wurde mit statischer IP (`10.30.0.20/24`) ohne Standardgateway und DNS konfiguriert. Jeglicher Outbound-Traffic ins Internet ist erfolgreich unterbunden.
- **Abnahme:** Isolationstest via Port 4 erfolgreich (kein Internetzugriff, aber voller Zugriff auf die Ziel-VM über Port 3000).

---

## 24.07.2026 - Fujitsu-Basisserver geprüft

### Gerät

- Modell: Fujitsu ESPRIMO Q556/2
- Prozessor: Intel Core i5-6500T, 4 Kerne / 4 Threads
- Arbeitsspeicher: 16 GB DDR4-2133, ein Modul, ein Steckplatz frei
- Datenträger: 512-GB-SATA-SSD
- Netzwerk: Gigabit-Ethernet
- BIOS: R1.35.0
- Kaufpreis: 97 EUR inklusive Versand

### Gemessene Abmessungen

- Breite: 185 mm
- Tiefe: 190 mm
- Höhe: 55 mm
- Standfüße: keine

### Testergebnisse

- [x] BIOS-Update erfolgreich
- [x] Prozessor, RAM und SSD korrekt erkannt
- [x] Virtualisierung aktiviert
- [x] Ethernet-Link mit 1 Gbit/s
- [x] IPv4- und IPv6-Verbindung ohne Paketverlust
- [x] Hardware- und Stabilitätstests ohne Fehler
- [x] CPU-Temperatur im Stresstest unter 70 Grad Celsius
- Allgemeinzustand: sehr gut, nur geringe Gebrauchsspuren

### Rack-Integration

- Geplant: 10-Zoll-Rack, 1,5 HE für den Fujitsu
- Halter-Innenmaß basiert auf 185 x 55 mm mit 0,8 mm Toleranz je Seite
- Gedruckte Stütztiefe: 160 mm
- Hinterer Überstand des Geräts: etwa 30 mm
- CAD-Datei: `Fujitsu_Q556_1_5U_A1_Mini.scad`

### Ursprünglich geplante Schritte (mittlerweile abgeschlossen)

- [x] Kurzen Passformtest der Halterung drucken
- [x] Rack fertigstellen
- [x] TP-Link-Switch einbauen und verkabeln
- [x] ESP32-Statusdisplay integrieren
- [x] Proxmox installieren und konfigurieren