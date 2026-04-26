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
    GPIO 13  → Bit 2
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
SW2_PINS = [33, 32, 13,  4]   # Schalter 2: gelb→rot

LEDS_PER_FIELD = 36    # LEDs pro Ampelfeld (4 Reihen à 9 LEDs im Zickzack)
NUM_FIELDS     = 3
TOTAL_LEDS     = LEDS_PER_FIELD * NUM_FIELDS   # = 108

BRIGHTNESS_NORMAL = 0.40   # 40% Helligkeit ist indoor absolut ausreichend (stromsparend)
BRIGHTNESS_ECO    = 0.10   # 10% Helligkeit im Schlafmodus (sehr stromsparend)
ECO_DELAY_MS      = 60000  # Nach 60 Sekunden Dauer-Grün wird abgedimmt

# Feldindizes im LED-Streifen (Streifen läuft von unten nach oben)
FIELD_GREEN  = 0   # unten
FIELD_YELLOW = 1   # Mitte
FIELD_RED    = 2   # oben

# Farben (Basiswerte unskaliert)
def _scale(r, g, b, brightness):
    return (int(r * brightness), int(g * brightness), int(b * brightness))

COLOR_OFF    = (0, 0, 0)
BASE_GREEN   = (0,   255, 0)
BASE_YELLOW  = (255, 200, 0)
BASE_RED     = (255, 0,   0)

# Lautstärkemessung
WINDOW_SIZE  = 25   # Gleitender Mittelwert über N Messungen (≈ 1,5 - 2 s)

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
    for field, color in [(FIELD_GREEN,  _scale(*BASE_GREEN, BRIGHTNESS_NORMAL)),
                         (FIELD_YELLOW, _scale(*BASE_YELLOW, BRIGHTNESS_NORMAL)),
                         (FIELD_RED,    _scale(*BASE_RED, BRIGHTNESS_NORMAL))]:
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
    pos1 = max(0, min(3, read_bcd(sw1)))   # Stellung 0-3 erzwingen
    pos2 = max(0, min(3, read_bcd(sw2)))

    t1 = THRESHOLDS_1[pos1]
    t2 = THRESHOLDS_2[pos2]

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
    start = time.ticks_ms()
    samples = []
    # Keine künstliche Pause! So schnell sampeln wie möglich für 50ms.
    while time.ticks_diff(time.ticks_ms(), start) < 50: 
        samples.append(mic.read())

    n = len(samples)
    if n == 0:
        return 0
    mean = sum(samples) / n
    variance = sum((s - mean) ** 2 for s in samples) / n
    return math.sqrt(variance)


# ── Hauptschleife ──────────────────────────────────────────────────────────────

startup_test()

rms_window = []
current_state = None
state_since = time.ticks_ms()

while True:
    rms = measure_rms()

    rms_window.append(rms)
    if len(rms_window) > WINDOW_SIZE:
        rms_window.pop(0)
    avg_rms = sum(rms_window) / len(rms_window)

    t1, t2 = read_thresholds()

    if avg_rms < t1:
        new_state = FIELD_GREEN
    elif avg_rms < t2:
        new_state = FIELD_YELLOW
    else:
        new_state = FIELD_RED

    if new_state != current_state:
        current_state = new_state
        state_since = time.ticks_ms()

    brightness = BRIGHTNESS_NORMAL
    if current_state == FIELD_GREEN and time.ticks_diff(time.ticks_ms(), state_since) > ECO_DELAY_MS:
        brightness = BRIGHTNESS_ECO

    if current_state == FIELD_GREEN:
        show(FIELD_GREEN, _scale(*BASE_GREEN, brightness))
    elif current_state == FIELD_YELLOW:
        show(FIELD_YELLOW, _scale(*BASE_YELLOW, brightness))
    else:
        show(FIELD_RED, _scale(*BASE_RED, brightness))
