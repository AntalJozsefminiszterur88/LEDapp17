# LEDapp/core/registry_utils.py

import os
import sys
import winreg

# Logolás (ha a reconnect_handler elérhető)
try:
    # Próbáljuk meg relatívan importálni
    from .reconnect_handler import log_event
except ImportError:
    # Vagy abszolútan, ha a core mappán kívülről hívják
    try:
        from core.reconnect_handler import log_event
    except ImportError:
        # Dummy logger végső esetben
        def log_event(msg):
            print(f"[LOG - Dummy RegistryUtils]: {msg}")


APP_NAME = "LEDApp"  # Az alkalmazás neve a registryben
# Fontos: A sys.executable adja meg a futtatható fájl (.exe) elérési útját PyInstaller után
# A futtatható fájl abszolút elérési útja.
APP_PATH = os.path.abspath(
    sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
)  # Ha scriptként fut, akkor a .py fájl

# Az indítópult registry kulcsa az aktuális felhasználóhoz
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_startup_command():
    """Összeállítja a parancsot, amit a registrybe írunk."""
    # Dupla idézőjelek közé tesszük az elérési utat, hogy kezelje a szóközöket
    # Hozzáadjuk a --tray argumentumot, hogy a tálcára minimalizálva induljon
    return f'"{APP_PATH}" --tray'  # Korábban --startup volt itt, de a --tray logikusabb


def add_to_startup():
    """Hozzáadja az alkalmazást az indítópulthoz a registryben."""
    try:
        # Ha a kulcs hiányzik, létrehozzuk
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
            command = _get_startup_command()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        log_event(f"Alkalmazás hozzáadva az indítópulthoz: '{command}'")
        return True
    except OSError as e:
        log_event(f"Hiba az indítópulthoz adás során: {e}")
        return False
    except Exception as e:
        log_event(f"Váratlan hiba az indítópulthoz adás során: {e}")
        return False


def remove_from_startup():
    """Eltávolítja az alkalmazást az indítópultból a registryben."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        log_event("Alkalmazás eltávolítva az indítópultból.")
        return True
    except FileNotFoundError:
        log_event("Alkalmazás nem volt az indítópultban (nem található a kulcs).")
        return True  # Nem hiba, ha már nincs ott
    except OSError as e:
        log_event(f"Hiba az indítópultból való eltávolítás során: {e}")
        return False
    except Exception as e:
        log_event(f"Váratlan hiba az indítópultból való eltávolítás során: {e}")
        return False


def is_in_startup():
    """Ellenőrzi, hogy az alkalmazás szerepel-e az indítópultban."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except OSError as e:
        log_event(f"Hiba az indítópult ellenőrzése során: {e}")
        return False  # Inkonzisztens állapot vagy jogosultsági hiba
    except Exception as e:
        log_event(f"Váratlan hiba az indítópult ellenőrzése során: {e}")
        return False
