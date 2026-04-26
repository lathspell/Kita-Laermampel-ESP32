# ESP32 einrichten: Schritt-für-Schritt

Dieses Dokument beschreibt, wie du MicroPython auf den ESP32 bekommst
und danach `main.py` auf das Gerät lädst. Kein Vorwissen über ESP32 nötig.

Geschrieben für **Linux** (Ubuntu/Debian). Windows-Abweichungen stehen am [Ende](#abweichungen-unter-windows).

## Inhaltsverzeichnis
- [Was du brauchst](#was-du-brauchst)
- [Schritt 1: Benutzer zur seriellen Gruppe hinzufügen](#schritt-1-benutzer-zur-seriellen-gruppe-hinzufügen-einmalig)
- [Schritt 2: Thonny installieren](#schritt-2-thonny-installieren-einmalig)
- [Schritt 3: ESP32 verbinden und prüfen](#schritt-3-esp32-verbinden-und-prüfen)
- [Schritt 4: MicroPython-Firmware flashen](#schritt-4-micropython-firmware-flashen)
- [Schritt 5: Verbindung testen (REPL)](#schritt-5-verbindung-testen-repl)
- [Schritt 6: main.py auf den ESP32 laden](#schritt-6-mainpy-auf-den-esp32-laden)
- [Schritt 7: Programm starten und testen](#schritt-7-programm-starten-und-testen)
- [Schritt 8: Kalibrierung](#schritt-8-kalibrierung-vor-dem-ersten-einsatz)
- [Schritt 9: Dauerbetrieb](#schritt-9-dauerbetrieb)
- [Abweichungen unter Windows](#abweichungen-unter-windows)
- [Häufige Probleme](#kurzreferenz-häufige-probleme)

## Was du brauchst

* ESP32 DevKit v1 (noch unbenutzt, frisch aus der Packung)
* USB-Kabel: **Micro-USB → USB-A** (nicht USB-C!) — **Datenkabel**, nicht nur Ladekabel
* Linux-Rechner mit Internetzugang (einmalig zum Herunterladen)
* Die Datei `main.py` aus diesem Projekt

## Schritt 1: Benutzer zur seriellen Gruppe hinzufügen (einmalig)

Linux schützt den Zugriff auf USB-Geräte mit Gruppenrechten.
Dieser Schritt ist einmalig nötig.

1. Terminal öffnen.
2. Folgenden Befehl eingeben:
   ```bash
   sudo usermod -aG dialout $USER
   ```
3. **Abmelden und neu anmelden** (oder den Rechner neu starten).
   Ohne diesen Schritt kann Thonny später nicht auf den ESP32 zugreifen.

## Schritt 2: Thonny installieren (einmalig)

Thonny ist eine einfache Python-IDE die MicroPython auf dem ESP32
direkt verwalten kann — Firmware flashen, Dateien übertragen, REPL nutzen.

```bash
sudo apt update && sudo apt install thonny
```

Falls `apt` das Paket nicht kennt (ältere Distributionen):

```bash
pip3 install thonny
```

Danach Thonny starten:

```bash
thonny
```

## Schritt 3: ESP32 verbinden und prüfen

1. ESP32 per USB anschließen.
2. Im Terminal prüfen ob das Gerät erkannt wurde:
   ```bash
   ls /dev/ttyUSB*
   ```
   Erwartete Ausgabe:
   ```
   /dev/ttyUSB0
   ```

> **Achtung:** Wenn nichts erscheint: anderes USB-Kabel probieren. Manche Micro-USB-Kabel
> haben keine Datenleitungen (nur Ladekabel). Mit `dmesg | tail -20` nach dem
> Anstecken prüfen ob der Kernel das Gerät meldet.

## Schritt 4: MicroPython-Firmware flashen

Dieser Schritt installiert MicroPython auf dem ESP32.
**Nur einmalig nötig** — `main.py` kann danach beliebig oft geändert werden.

1. Thonny starten.
2. Menü **Tools → Options** → Reiter **Interpreter**.
3. Dropdown *„Which kind of interpreter…"* → **MicroPython (ESP32)** wählen.
4. Darunter den Link **„Install or update MicroPython (esptool)"** anklicken.
   Ein neues Fenster öffnet sich.
5. Im Fenster einstellen:

   | Feld | Wert |
   |---|---|
   | Target port | `/dev/ttyUSB0` |
   | MicroPython family | `ESP32` |
   | Variant | `Espressif ESP32 / WROOM` (Standardauswahl) |
   | Version | neueste stabile Version (ganz oben in der Liste) |

6. **„Install"** klicken und warten (~30 Sekunden).
   Die Statusleiste zeigt den Fortschritt. Am Ende erscheint **„Done"**.
7. Fenster schließen, dann **OK**.

> **Achtung:** Während des Flashens den USB-Stecker **nicht** abziehen.

## Schritt 5: Verbindung testen (REPL)

Das REPL (Read-Eval-Print Loop) ist eine interaktive Python-Konsole
direkt auf dem ESP32. Damit prüfst du ob alles funktioniert.

1. In Thonny: unten erscheint ein Bereich mit `>>>` — das ist das REPL.
2. Falls es nicht erscheint: Menü **View → Shell** aktivieren.
3. Klicke in den unteren Bereich und tippe:
   ```python
   print("Hallo ESP32")
   ```
   Erwartete Ausgabe direkt darunter:
   ```
   Hallo ESP32
   ```

> **Hinweis:** Falls `>>>` nicht erscheint: den roten **Stopp-Button** in der Toolbar drücken,
> oder ESP32 kurz abstecken und neu anstecken.

## Schritt 6: main.py auf den ESP32 laden

1. In Thonny: Menü **File → Open…**
2. Im Dialogfenster unten: **„This computer"** wählen.
3. `main.py` aus dem Projektordner öffnen — die Datei erscheint im Editor.
4. Menü **File → Save as…**
5. Im Dialogfenster unten: **„MicroPython device"** wählen.
6. Dateiname **`main.py`** lassen — **genau so schreiben**.

> **Wichtig:** MicroPython startet beim Einschalten automatisch die Datei mit dem
> Namen `main.py`. Jeder andere Name wird ignoriert.

7. **Speichern** klicken.
8. Kontrolle: Menü **View → Files** → im rechten Bereich unter
   **„MicroPython device"** sollte `main.py` erscheinen.

## Schritt 7: Programm starten und testen

1. Roten **Stopp-Button** in Thonny drücken.
2. Grünen **Start-Button** (▶) drücken — *oder* ESP32 kurz abstecken und neu anstecken.
3. Wenn LEDs angeschlossen sind: Selbsttest läuft ab (grün → gelb → rot → aus).
4. Danach geht die Ampel in den normalen Messbetrieb.

> **Hinweis:** Ohne angeschlossene LEDs läuft das Programm trotzdem durch — es erscheint
> kein Fehler, weil der LED-Pin einfach nur ein Signal sendet das niemand empfängt.

## Schritt 8: Kalibrierung (vor dem ersten Einsatz)

Die Schwellwerte in `main.py` (`THRESHOLDS_1`, `THRESHOLDS_2`) sind Schätzwerte.
Der tatsächliche Messwert hängt vom Gain-Trimmer auf dem MAX4466-Modul ab.
So findest du die richtigen Werte für deinen Raum:

1. MAX4466 per Kabel mit ESP32 verbinden (Kabel 3, 4, 9 aus der Verkabelungsliste).
2. In Thonny: roten Stopp-Button drücken bis `>>>` erscheint.
3. Folgenden Code **komplett** markieren, kopieren und ins REPL einfügen, dann Enter:

   ```python
   import machine, math, time
   mic = machine.ADC(machine.Pin(34))
   mic.atten(machine.ADC.ATTN_11DB)
   def rms():
       s = [mic.read() for _ in range(50) if not time.sleep_ms(2)]
       m = sum(s) / len(s)
       return math.sqrt(sum((x - m) ** 2 for x in s) / len(s))
   while True:
       print(round(rms(), 1))
       time.sleep_ms(500)
   ```

4. Der ESP32 gibt jetzt alle 0,5 Sekunden den aktuellen RMS-Wert aus.
5. Notiere die Werte für verschiedene Lautstärken:

   | Situation | RMS-Wert (aufschreiben) |
   |---|---|
   | Stille (niemand im Raum) | ___________ |
   | Leises Gespräch | ___________ |
   | Normale Gruppenaktivität | ___________ |
   | Laute Gruppe / Rufen | ___________ |

6. Mit **Ctrl+C** den Messmodus stoppen.
7. `main.py` im Editor öffnen und die Schwellwert-Arrays anpassen:

   ```python
   # Beispiel anhand gemessener Werte:
   #   Stille=12, Leise=40, Normal=90, Laut=220
   THRESHOLDS_1 = [25,  50,  80, 120]   # grün→gelb Stellung 1–4
   THRESHOLDS_2 = [60, 100, 160, 280]   # gelb→rot  Stellung 1–4
   ```

8. `main.py` erneut auf den ESP32 speichern (Schritt 6 wiederholen).
9. Drehschalter mit den gewählten Werten beschriften.

> **Hinweis:** Den kleinen Gain-Trimmer auf dem MAX4466-Modul kannst du mit einem
> Uhrmacher-Schraubenzieher verstellen um den Messbereich zu verschieben —
> nützlich wenn die Werte zu nah beieinander liegen.

## Schritt 9: Dauerbetrieb

Sobald `main.py` auf dem ESP32 gespeichert ist, startet das Programm
**automatisch** bei jedem Einschalten — ohne Laptop, ohne Thonny.

Das USB-Netzteil reicht, der Laptop ist nicht mehr nötig.

## Abweichungen unter Windows

Alles oben Beschriebene funktioniert unter Windows fast identisch,
mit folgenden Unterschieden:

| Schritt | Windows-Abweichung |
|---|---|
| Schritt 1 (Gruppenrechte) | Entfällt komplett — unter Windows nicht nötig. |
| Schritt 2 (Thonny) | Installer (`.exe`) von https://thonny.org herunterladen und ausführen. Kein Terminal nötig. |
| Schritt 3 (Port prüfen) | Statt `/dev/ttyUSB0` heißt der Port `COM3`, `COM4` o.ä. Nachsehen unter: **Geräte-Manager → Anschlüsse (COM & LPT)**. Falls kein COM-Port erscheint: CP2102-Treiber von der silabs.com-Website herunterladen und installieren, dann Neustart. |
| Schritt 4 (Firmware) | Im Thonny-Fenster unter **Target port** den COM-Port (z.B. `COM3`) wählen. Alles andere identisch. |
| Schritt 5–9 | Vollständig identisch mit Linux. |

## Kurzreferenz: Häufige Probleme

| Problem | Lösung |
|---|---|
| `/dev/ttyUSB*` leer nach Anstecken | Anderes USB-Kabel probieren (Datenkabel). `dmesg \| tail -20` zeigt ob der Kernel das Gerät überhaupt sieht. |
| `could not connect` in Thonny | Roten Stopp-Button drücken; ESP32 kurz abstecken und neu anstecken. Sicherstellen dass kein anderes Programm den Port belegt. |
| Thonny fragt nach Port aber keiner erscheint | Schritt 1 (Gruppenrechte) vergessen → abmelden und neu anmelden. |
| Programm startet nicht (kein Selbsttest) | Im REPL: `import main` eingeben — Fehlermeldung zeigt die Ursache. |
| `AssertionError: Konfigurationsfehler` | `THRESHOLDS_1` max ≥ `THRESHOLDS_2` min in `main.py` — Werte anpassen. |
| LEDs leuchten nicht | Verkabelung prüfen: WS2812B VCC muss an **VIN** (5 V), nicht an 3V3. |
