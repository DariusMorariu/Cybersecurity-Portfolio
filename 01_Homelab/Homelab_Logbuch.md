# Homelab-Logbuch

Dieses Logbuch wird während des Aufbaus laufend ergänzt. Aus den Einträgen
entsteht später die fertige Word-Dokumentation für das Portfolio.

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

- BIOS-Update erfolgreich
- Prozessor, RAM und SSD korrekt erkannt
- Virtualisierung aktiviert
- Ethernet-Link mit 1 Gbit/s
- IPv4- und IPv6-Verbindung ohne Paketverlust
- Hardware- und Stabilitätstests ohne Fehler
- CPU-Temperatur im Stresstest unter 70 Grad Celsius
- Allgemeinzustand: sehr gut, nur geringe Gebrauchsspuren

### Rack-Integration

- Geplant: 10-Zoll-Rack, 1,5 HE für den Fujitsu
- Halter-Innenmaß basiert auf 185 x 55 mm mit 0,8 mm Toleranz je Seite
- Gedruckte Stütztiefe: 160 mm
- Hinterer Überstand des Geräts: etwa 30 mm
- CAD-Datei: `Fujitsu_Q556_1_5U_A1_Mini.scad`

### Nächste Schritte

- Kurzen Passformtest der Halterung drucken
- Rack fertigstellen
- TP-Link-Switch einbauen und verkabeln
- ESP32-Statusdisplay integrieren
- Proxmox zu einem späteren Zeitpunkt installieren
