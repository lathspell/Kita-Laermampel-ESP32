# Kita-Lärmampel: Verkabelung

## Inhaltsverzeichnis
- [Übersicht](#übersicht-mermaid-diagramm)
- [Kabel für Kabel](#kabel-für-kabel)
- [Checkliste vor dem ersten Start](#checkliste-vor-dem-ersten-start)

## Übersicht (Mermaid-Diagramm)

```mermaid
graph LR
    subgraph ESP32["ESP32 DevKit v1"]
        VIN["VIN (5V)"]
        V33["3V3"]
        GNDE["GND"]
        G5["GPIO 5"]
        G34["GPIO 34"]
        G25["GPIO 25"]
        G26["GPIO 26"]
        G27["GPIO 27"]
        G14["GPIO 14"]
        G33P["GPIO 33"]
        G32["GPIO 32"]
        G15["GPIO 15"]
        G4["GPIO 4"]
    end

    R["Widerstand\n330-470 Ohm"]

    subgraph WS["WS2812B LED-Streifen"]
        WVCC["VCC"]
        WGND["GND"]
        WDIN["DIN"]
    end

    subgraph MIC["MAX4466 Mikrofon"]
        MVCC["VCC"]
        MGND["GND"]
        MOUT["OUT"]
    end

    subgraph SW1["Leise-Regler (BCD-Schalter)"]
        S1C["C (Common)"]
        S11["Pin 1 (Bit 0)"]
        S12["Pin 2 (Bit 1)"]
        S14["Pin 4 (Bit 2)"]
        S18["Pin 8 (Bit 3)"]
    end

    subgraph SW2["Laut-Regler (BCD-Schalter)"]
        S2C["C (Common)"]
        S21["Pin 1 (Bit 0)"]
        S22["Pin 2 (Bit 1)"]
        S24["Pin 4 (Bit 2)"]
        S28["Pin 8 (Bit 3)"]
    end

    VIN --- WVCC
    GNDE --- WGND
    GNDE --- MGND
    GNDE --- S1C
    GNDE --- S2C
    G5 --- R --- WDIN
    V33 --- MVCC
    G34 --- MOUT
    G25 --- S11
    G26 --- S12
    G27 --- S14
    G14 --- S18
    G33P --- S21
    G32 --- S22
    G15 --- S24
    G4 --- S28
```

## Kabel für Kabel

Jede Zeile = ein Kabel (oder eine direkte Lötverbindung).

### Stromversorgung

| # | Von | Nach | Hinweis |
|---|---|---|---|
| 1 | ESP32 **VIN** | WS2812B **VCC** | 5 V, rot |
| 2 | ESP32 **GND** | WS2812B **GND** | schwarz |
| 3 | ESP32 **3V3** | MAX4466 **VCC** | 3,3 V, rot |
| 4 | ESP32 **GND** | MAX4466 **GND** | schwarz |
| 5 | ESP32 **GND** | Leise-Regler **C (Common)** | schwarz |
| 6 | ESP32 **GND** | Laut-Regler **C (Common)** | schwarz |

> **Hinweis:** Die GND-Kabel 2, 4, 5, 6 teilen sich denselben GND-Pin am ESP32.
> Auf einem Breadboard legt man alle auf die GND-Schiene; beim Löten
> kann man sie zusammen auf einen Pin führen.

### Datenleitung LED-Streifen

| # | Von | Nach | Hinweis |
|---|---|---|---|
| 7 | ESP32 **GPIO 5** | Widerstand **Seite A** | beliebige Farbe |
| 8 | Widerstand **Seite B** | WS2812B **DIN** | beliebige Farbe |

> **Hinweis:** Der Widerstand (330–470 Ω) liegt **in Serie** auf der Datenleitung —
> d.h. er unterbricht das Kabel zwischen GPIO 5 und DIN.
> Polarität spielt bei Widerständen keine Rolle.

### Mikrofon

| # | Von | Nach | Hinweis |
|---|---|---|---|
| 9 | ESP32 **GPIO 34** | MAX4466 **OUT** | beliebige Farbe |

### Leise-Regler (BCD-Schalter, grün→gelb)

| # | Von | Nach | Hinweis |
|---|---|---|---|
| 10 | ESP32 **GPIO 25** | Leise-Regler **Pin 1** | Bit 0 |
| 11 | ESP32 **GPIO 26** | Leise-Regler **Pin 2** | Bit 1 |
| 12 | ESP32 **GPIO 27** | Leise-Regler **Pin 4** | Bit 2 |
| 13 | ESP32 **GPIO 14** | Leise-Regler **Pin 8** | Bit 3 |

> **Hinweis:** Die Pins am BCD-Schalter sind mit **1, 2, 4, 8** beschriftet
> (Binärwertigkeit, nicht laufende Nummern). Common (C) wurde bereits in Kabel 5 verdrahtet.

### Laut-Regler (BCD-Schalter, gelb→rot)

| # | Von | Nach | Hinweis |
|---|---|---|---|
| 14 | ESP32 **GPIO 33** | Laut-Regler **Pin 1** | Bit 0 |
| 15 | ESP32 **GPIO 32** | Laut-Regler **Pin 2** | Bit 1 |
| 16 | ESP32 **GPIO 15** | Laut-Regler **Pin 4** | Bit 2 |
| 17 | ESP32 **GPIO  4** | Laut-Regler **Pin 8** | Bit 3 |

## Checkliste vor dem ersten Start

- [ ] Alle 17 Verbindungen hergestellt
- [ ] Kein GND-Kabel vergessen (Kabel 2, 4, 5, 6)
- [ ] Widerstand liegt **zwischen** GPIO 5 und WS2812B DIN, nicht parallel
- [ ] WS2812B VCC an **VIN** (5 V), nicht an 3V3
- [ ] MAX4466 VCC an **3V3**, nicht an VIN
- [ ] USB-Netzteil noch **nicht** eingesteckt beim Verdrahten
