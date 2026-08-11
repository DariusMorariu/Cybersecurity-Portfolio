# Homelab-Logbuch

Dieses Logbuch wird während des Aufbaus laufend ergänzt. Aus den Einträgen
entsteht später die fertige Word-Dokumentation für das Portfolio.

## 11.08.2026 - Finaler Build, Proxmox & Hacking-Lab

### Hardware-Build & 3D-Druck
- 10-Zoll-Rack (inklusive Halterungen für den Fujitsu und den Switch) vollständig auf dem Bambu Lab A1 Mini gedruckt und final montiert.
- Arbeitsspeicher des Fujitsu erfolgreich auf 32 GB DDR4 SO-DIMM (Non-ECC) aufgerüstet (anfängliches Kompatibilitätsproblem mit ECC-RAM gelöst).
- TP-Link-Switch und 8-Port-Keystone-Patchpanel physisch in das Rack integriert und mit kurzen Patchkabeln sauber verkabelt.
- ESP32 samt 3,5-Zoll-ILI9488-Touchdisplay in die gedruckte Frontblende eingebaut und erfolgreich verdrahtet (SPI-Bus).

### Software & Virtualisierung
- Proxmox VE als Typ-1-Hypervisor installiert und konfiguriert.
- LXC-Container (ID 100, `middleware-ui`) für das ESP32-Backend mit Node.js und PM2 aufgesetzt. Ressourcenverbrauch optimal bei ca. 75 MB RAM.
- Erste Ziel-VM (ID 101, `juice-shop`) mit Ubuntu Server 24.04 LTS erstellt und OWASP Juice Shop als Docker-Container deployt.

### Netzwerk & Security-Isolation
- 802.1Q VLAN-Trunking auf dem TP-Link TL-SG108E Switch aktiv eingerichtet.
- **VLAN 1:** Heimnetz und Proxmox-Management (Untagged).
- **VLAN 30 (Cyber-Lab):** Isoliertes Hacking-Netz (Port 3 Tagged, Port 4 Untagged für den dedizierten Angreifer-Laptop).
- Virtueller Proxmox-Switch (`vmbr0`) arbeitet "VLAN aware".
- **Netzwerk-Härtung:** Die Ubuntu-VM (Juice Shop) wurde mit statischer IP (`10.30.0.20/24`) ohne Standardgateway und DNS konfiguriert. Jeglicher Outbound-Traffic ins Internet ist erfolgreich unterbunden.
- **Abnahme:** Isolationstest via Port 4 erfolgreich (kein Internetzugriff, aber voller Zugriff auf die Ziel-VM über Port 3000).

### Nächste Schritte
- Statusdaten des Proxmox-Hosts (CPU, RAM, Netzwerk) an den ESP32 übertragen und auf dem Display grafisch aufbereiten.
- Weitere verwundbare Zielsysteme (z. B. via Hack The Box oder VulnHub) im VLAN 30 ausrollen.
- Backup- und Wiederherstellungskonzept für die VMs testen.

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