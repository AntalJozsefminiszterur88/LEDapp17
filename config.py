from pathlib import Path
import json
import os

LATITUDE = 47.4338
LONGITUDE = 19.1931
TIMEZONE = "UTC+2"

# Alap könyvtár: Dokumentumok/UMKGL Solutions/LEDapp
BASE_DIR = Path.home() / "Documents" / "UMKGL Solutions" / "LEDapp"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Az ütemezés fájl teljes elérési útja
CONFIG_FILE = str(BASE_DIR / "led_schedule.json")
# Új fájl az ütemezési profilok tárolásához
PROFILES_FILE = str(BASE_DIR / "led_schedule_profiles.json")

CUSTOM_COLORS_FILE = str(BASE_DIR / "custom_colors.json")

# ---- Egyedi színek kezelése ----
def load_custom_colors():
    """Betölti az egyedi színeket a fájlból."""
    path = CUSTOM_COLORS_FILE
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            colors = []
            for item in data:
                name = item.get("name")
                hex_color = item.get("hex_color")
                command_hex = item.get("command_hex")
                if name and hex_color and command_hex:
                    colors.append((name, hex_color, command_hex))
            return colors
        except Exception as e:
            print(f"Hiba az egyedi színek betöltésekor: {e}")
    return []


def save_custom_colors(colors):
    """Elmenti az egyedi színeket a fájlba."""
    path = CUSTOM_COLORS_FILE
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {"name": n, "hex_color": c, "command_hex": h}
                    for n, c, h in colors
                ],
                f,
                ensure_ascii=False,
                indent=4,
            )
        return True
    except Exception as e:
        print(f"Hiba az egyedi színek mentésekor: {e}")
        return False


CUSTOM_COLORS = load_custom_colors()

CHARACTERISTIC_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

DAYS = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]

COLORS = [
    ("Piros", "#ff0000", "7e000503ff000000ef"),
    ("Zöld", "#00ff00", "7e00050300ff0000ef"),
    ("Kék", "#0000ff", "7e0005030000ff00ef"),
    ("Sárga", "#ffff00", "7e000503ffff0000ef"),
    ("Cian", "#00ffff", "7e00050300ffff00ef"),
    ("Lila", "#800080", "7e00050380008000ef"),
    ("Narancs", "#ffa500", "7e000503ffa50000ef"),
    ("Fehér", "#ffffff", "7e000503ffffff00ef")
]

# Beépített és egyedi színek összevonása
if CUSTOM_COLORS:
    COLORS.extend(CUSTOM_COLORS)


def add_custom_color(name: str, hex_color: str):
    """Hozzáad egy új egyedi színt és elmenti."""
    if not name or not hex_color:
        return None
    hex_clean = hex_color.lstrip("#")
    command = f"7e000503{hex_clean.lower()}00ef"
    entry = (name, f"#{hex_clean}", command)
    # Ne legyen duplikált név
    for c in COLORS:
        if c[0] == name:
            return None
    COLORS.append(entry)
    CUSTOM_COLORS.append(entry)
    save_custom_colors(CUSTOM_COLORS)
    return entry


def remove_custom_color(name: str):
    """Töröl egy egyedi színt név alapján."""
    removed = False
    for lst in (CUSTOM_COLORS, COLORS):
        for item in list(lst):
            if item[0] == name:
                lst.remove(item)
                removed = True
    if removed:
        save_custom_colors(CUSTOM_COLORS)
    return removed
