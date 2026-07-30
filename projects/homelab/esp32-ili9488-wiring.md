# ESP32 mit ILI9488-Display und Touchscreen

Diese Pinbelegung wurde mit einem ESP32 und einem 3,5-Zoll-TFT-Modul mit
ILI9488-Controller erfolgreich getestet. Display und Touchscreen verwenden
denselben SPI-Takt und dieselbe MOSI-Leitung.

## Stromversorgung und Hintergrundbeleuchtung

| Display-Pin | ESP32-Pin | Anmerkung |
|---|---|---|
| `VCC` | `5V` / `VIN` | Hauptstromversorgung des Displays |
| `GND` | `GND` | Gemeinsame Masse |
| `LED` / `BL` | `3V3` | Versorgung der Hintergrundbeleuchtung bei diesem Modul |

> **Wichtig:** Bei diesem getesteten Modul wird `LED` beziehungsweise `BL` mit
> 3,3 V versorgt. Vor dem Anschluss eines anderen Moduls sollte dessen
> Pinbelegung kontrolliert werden.

## Display

| Display-Pin | ESP32-Pin | Anmerkung |
|---|---|---|
| `CS` | `GPIO 27` | Chip Select des Displays |
| `RESET` / `RST` | `GPIO 26` | Reset-Leitung |
| `DC` / `RS` | `GPIO 25` | Data/Command |
| `SDI` / `MOSI` | `GPIO 23` | SPI-Datenleitung, gemeinsam mit dem Touchscreen |
| `SCK` / `CLK` | `GPIO 18` | SPI-Takt, gemeinsam mit dem Touchscreen |
| `SDO` / `MISO` | Nicht verbunden | Eine Verbindung blockierte bei diesem Modul im Test den SPI-Bus |

## Touchscreen

| Touch-Pin | ESP32-Pin | Anmerkung |
|---|---|---|
| `T_CLK` | `GPIO 18` | Gemeinsamer SPI-Takt |
| `T_CS` | `GPIO 33` | Chip Select des Touch-Controllers |
| `T_DIN` / `T_IN` | `GPIO 23` | Gemeinsame MOSI-Leitung |
| `T_OUT` / `T_DO` | `GPIO 19` | MISO-Leitung vom Touch-Controller zum ESP32 |
| `T_IRQ` | `GPIO 32` | Interrupt-Leitung; im aktuellen Testcode optional |

## Verdrahtungsübersicht

```text
ILI9488 / Touch             ESP32
---------------------------------
VCC                  ->     5V / VIN
GND                  ->     GND
LED / BL             ->     3V3

CS                   ->     GPIO 27
RESET / RST          ->     GPIO 26
DC / RS              ->     GPIO 25
SDI / MOSI           ->     GPIO 23
SCK / CLK            ->     GPIO 18
SDO / MISO           ->     nicht verbunden

T_CLK                ->     GPIO 18
T_CS                 ->     GPIO 33
T_DIN / T_IN         ->     GPIO 23
T_OUT / T_DO         ->     GPIO 19
T_IRQ                ->     GPIO 32
```

## Ergebnis

- Bildausgabe funktioniert.
- Hintergrundbeleuchtung funktioniert.
- Touch-Eingabe funktioniert.
- Display und Touchscreen arbeiten gemeinsam am SPI-Bus.

