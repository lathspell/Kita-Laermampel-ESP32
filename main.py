"""
Kita-Lärmampel — MicroPython / ESP32
=====================================
Zeigt den Geräuschpegel als grün/gelb/rot an.
Zwei kodierte Drehschalter (BCD, 10-stufig) stellen die Schwellwerte ein.

Verdrahtung
-----------
  GPIO  5  → WS2812B Datenleitung
  GPIO 34  → MAX4466 Ausgang  (ADC1, Input-only)

  Drehschalter 1 — grün→gelb  (Common → GND)
    GPIO 25  → Bit 0
    GPIO 26  → Bit 1
    GPIO 27  → Bit 2
    GPIO 14  → Bit 3

  Drehschalter 2 — gelb→rot  (Common → GND)
    GPIO 33  → Bit 0
    GPIO 32  → Bit 1
    GPIO 15  → Bit 2
    GPIO  4  → Bit 3

  GND / 3V3 → Mikrofon-Modul (VCC an 3V3)

Schalter-Beschriftung (4 genutzte Stufen)
  Stellung 1 = leise     Stellung 3 = mittel-laut
  Stellung 2 = mittel    Stellung 4 = laut
  (konkrete dB-Werte nach Kalibrierung des MAX4466-Gain-Trimmers eintragen)

Kalibrierung
------------
  1. MAX4466 Gain-Trimmer so einstellen, dass measure_rms() im normalen
     Kita-Betrieb sinnvolle Werte liefert (per REPL prüfen).
  2. THRESHOLDS_1 und THRESHOLDS_2 entsprechend anpassen.
  3. Schalter-Beschriftungen mit den realen dB-Werten bedrucken/bekleben.
"""

import machine
import neopixel
import time
import math

# ── Konfiguration ──────────────────────────────────────────────────────────────

LED_PIN = 5     # WS2812B Datenleitung
MIC_PIN = 34    # MAX4466 Ausgang (ADC1, Input-only Pin)

# BCD-Drehschalter: Bit-Pins in aufsteigender Wertigkeit [bit0, bit1, bit2, bit3]
# Common-Pin jedes Schalters → GND; interne Pull-ups aktiv
SW1_PINS = [25, 26, 27, 14]   # Schalter 1: grün→gelb
SW2_PINS = [33, 32, 15,  4]   # Schalter 2: gelb→rot

LEDS_PER_FIELD = 36    # LEDs pro Ampelfeld (4 Reihen à 9 LEDs im Zickzack)
NUM_FIELDS     = 3
TOTAL_LEDS     = LEDS_PER_FIELD * NUM_FIELDS   # = 108

BRIGHTNESS = 0.6   # 60% → Worst Case ~1.16 A, sicher für 1.5 A USB-Netzteil

# Feldindizes im LED-Streifen (Streifen läuft von unten nach oben)
FIELD_GREEN  = 0   # unten
FIELD_YELLOW = 1   # Mitte
FIELD_RED    = 2   # oben

# Farben (skaliert auf BRIGHTNESS)
def _scale(r, g, b):
    return (int(r * BRIGHTNESS), int(g * BRIGHTNESS), int(b * BRIGHTNESS))

COLOR_GREEN  = _scale(0,   255, 0)
COLOR_YELLOW = _scale(255, 200, 0)
COLOR_RED    = _scale(255, 0,   0)
COLOR_OFF    = (0, 0, 0)

# Lautstärkemessung
ADC_SAMPLES  = 50   # Samples pro RMS-Messung  (50 × 2 ms ≈ 100 ms/Messung)
SAMPLE_DELAY = 2    # ms zwischen ADC-Samples
WINDOW_SIZE  = 5    # Gleitender Mittelwert über N Messungen (≈ 0.5 s)

# Schwellwerte in RMS-Einheiten für die 4 Schalterstellungen (Index 0 = Stellung 1)
# !! Nach Kalibrierung des MAX4466 anpassen !!
#
# Wichtig: max(THRESHOLDS_1) muss kleiner sein als min(THRESHOLDS_2),
# damit keine ungültige Kombination möglich ist — unabhängig von der Schalterstellung.
THRESHOLDS_1 = [ 60,  90, 130, 170]   # grün→gelb: leise … laut  (max = 170)
THRESHOLDS_2 = [200, 280, 380, 550]   # gelb→rot:  leise … laut  (min = 200)

assert max(THRESHOLDS_1) < min(THRESHOLDS_2), (
    "Konfigurationsfehler: THRESHOLDS_1 max={} >= THRESHOLDS_2 min={}".format(
        max(THRESHOLDS_1), min(THRESHOLDS_2)
    )
)


# ── Hardware-Setup ─────────────────────────────────────────────────────────────

np = neopixel.NeoPixel(machine.Pin(LED_PIN), TOTAL_LEDS)

mic = machine.ADC(machine.Pin(MIC_PIN))
mic.atten(machine.ADC.ATTN_11DB)   # 0–3.3 V Eingansbereich

sw1 = [machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP) for p in SW1_PINS]
sw2 = [machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP) for p in SW2_PINS]


# ── LED-Hilfsfunktionen ────────────────────────────────────────────────────────

def _set_field(field, color):
    """Setzt alle LEDs eines Feldes auf 'color', ohne np.write()."""
    start = field * LEDS_PER_FIELD
    for i in range(start, start + LEDS_PER_FIELD):
        np[i] = color


def show(active_field, color):
    """Leuchtet 'active_field' in 'color', alle anderen Felder aus."""
    for field in range(NUM_FIELDS):
        _set_field(field, color if field == active_field else COLOR_OFF)
    np.write()


def all_off():
    for i in range(TOTAL_LEDS):
        np[i] = COLOR_OFF
    np.write()


def startup_test():
    """Selbsttest: Grün → Gelb → Rot → Aus."""
    for field, color in [(FIELD_GREEN,  COLOR_GREEN),
                         (FIELD_YELLOW, COLOR_YELLOW),
                         (FIELD_RED,    COLOR_RED)]:
        _set_field(field, color)
        np.write()
        time.sleep_ms(500)
    time.sleep_ms(300)
    all_off()
    time.sleep_ms(300)


# ── Schalter-Auslesen ──────────────────────────────────────────────────────────

def read_bcd(pins):
    """
    Liest einen BCD-Drehschalter aus. Common-Pin liegt an GND,
    aktive Bit-Pins sind LOW (interne Pull-ups ziehen inaktive auf HIGH).
    Gibt den dekodieren Stellungswert zurück (1–10 für einen 10-stufigen Schalter).
    """
    val = 0
    for i, pin in enumerate(pins):
        if not pin.value():   # LOW = aktiv = dieser Bit gesetzt
            val |= (1 << i)
    return val


def read_thresholds():
    """
    Liest beide Drehschalter und gibt (schwelle_1, schwelle_2) zurück.
    Schalterstellung außerhalb 1–4 wird auf die nächste gültige Grenze geklemmt.
    Garantiert: schwelle_2 > schwelle_1.
    """
    pos1 = max(1, min(4, read_bcd(sw1)))   # Stellung 1–4 erzwingen
    pos2 = max(1, min(4, read_bcd(sw2)))

    t1 = THRESHOLDS_1[pos1 - 1]
    t2 = THRESHOLDS_2[pos2 - 1]

    # Sicherheitsnetz: gelb/rot-Schwelle muss über grün/gelb-Schwelle liegen
    if t2 <= t1:
        t2 = t1 + 30
    return t1, t2


# ── Lautstärkemessung ──────────────────────────────────────────────────────────

def measure_rms():
    """
    Misst den Schallpegel als RMS des AC-Anteils des Mikrofonsignals.
    Der DC-Offset (Ruhe-Gleichspannung des MAX4466) wird herausgerechnet.
    """
    samples = []
    for _ in range(ADC_SAMPLES):
        samples.append(mic.read())
        time.sleep_ms(SAMPLE_DELAY)
    mean = sum(samples) / ADC_SAMPLES
    variance = sum((s - mean) ** 2 for s in samples) / ADC_SAMPLES
    return math.sqrt(variance)


# ── Hauptschleife ──────────────────────────────────────────────────────────────

startup_test()

rms_window = []

while True:
    rms = measure_rms()

    rms_window.append(rms)
    if len(rms_window) > WINDOW_SIZE:
        rms_window.pop(0)
    avg_rms = sum(rms_window) / len(rms_window)

    t1, t2 = read_thresholds()

    if avg_rms < t1:
        show(FIELD_GREEN, COLOR_GREEN)
    elif avg_rms < t2:
        show(FIELD_YELLOW, COLOR_YELLOW)
    else:
        show(FIELD_RED, COLOR_RED)
