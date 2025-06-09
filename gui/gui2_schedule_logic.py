# LEDapp/gui/gui2_schedule_logic.py

import json
import os
from datetime import datetime, timedelta, time as dt_time
import traceback
import pytz

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

# Importáljuk a szükséges konfigurációs és backend/core elemeket
from config import COLORS, DAYS, CONFIG_FILE, PROFILES_FILE
from core.sun_logic import get_local_sun_info, get_hungarian_day_name, DAYS_HU
from core.location_utils import get_sun_times # Bár itt nincs közvetlen hívás, a main_app tartalmazza

# --- Időzóna Definíció ---
# Biztosítjuk, hogy a LOCAL_TZ létezzen
try:
    # Próbáljuk meg a rendszer alapértelmezett időzónáját használni, ha lehetséges
    try:
        import tzlocal
        LOCAL_TZ = tzlocal.get_localzone()
        print(f"Helyi időzóna (tzlocal - logic): {LOCAL_TZ.zone}")
    except ImportError:
        # Ha a tzlocal nincs telepítve, maradunk a fixnél
        LOCAL_TZ = pytz.timezone("Europe/Budapest")
        print(f"Helyi időzóna (fix - logic): {LOCAL_TZ.zone}")
except pytz.UnknownTimeZoneError:
    print("Figyelmeztetés: Helyi időzóna nem található. UTC használata (logic).")
    LOCAL_TZ = pytz.utc
except Exception as e:
    print(f"Váratlan hiba az időzóna beolvasásakor (logic): {e}. UTC használata.")
    LOCAL_TZ = pytz.utc

# --- Logika Függvények ---

def get_default_schedule():
    """Alapértelmezett ütemezés létrehozása."""
    return {
        day: {
            "color": COLORS[0][0] if COLORS else "",
            "on_time": "",
            "off_time": "",
            "sunrise": False,
            "sunrise_offset": 0,
            "sunset": False,
            "sunset_offset": 0,
        }
        for day in DAYS
    }


def load_profiles_from_file(main_app):
    """Betölti az ütemezési profilokat."""
    default_schedule = get_default_schedule()
    default_profiles = {"Alapértelmezett": {"active": True, "schedule": default_schedule}}

    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            profiles = {}
            for name, prof in data.items():
                active = bool(prof.get("active", True))
                sched = prof.get("schedule", {})
                merged = {}
                for day in DAYS:
                    d = default_schedule[day].copy()
                    if day in sched and isinstance(sched[day], dict):
                        for key in d:
                            if key in sched[day]:
                                val = sched[day][key]
                                if key.endswith("_offset"):
                                    try:
                                        d[key] = int(val)
                                    except (ValueError, TypeError):
                                        d[key] = 0
                                elif isinstance(val, type(d[key])):
                                    d[key] = val
                    merged[day] = d
                profiles[name] = {"active": active, "schedule": merged}

            if profiles:
                main_app.profiles = profiles
                return
        except Exception as e:
            print(f"Hiba a profilok betöltésekor: {e}")

    # Visszafelé kompatibilitás: régi egyprofilos fájl
    single_schedule = default_schedule.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for day in DAYS:
                d = single_schedule[day].copy()
                if day in loaded and isinstance(loaded[day], dict):
                    for key in d:
                        if key in loaded[day]:
                            val = loaded[day][key]
                            if key.endswith("_offset"):
                                try:
                                    d[key] = int(val)
                                except (ValueError, TypeError):
                                    d[key] = 0
                            elif isinstance(val, type(d[key])):
                                d[key] = val
                single_schedule[day] = d
        except Exception as e:
            print(f"Hiba a régi ütemezés betöltésekor: {e}")

    main_app.profiles = {"Alapértelmezett": {"active": True, "schedule": single_schedule}}


def _save_profiles_to_file(main_app):
    """Segédfüggvény a profilok mentéséhez."""
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(main_app.profiles, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Hiba a profilok mentésekor: {e}")
        return False


def validate_profile(profile):
    """Ellenőrzi, hogy a profil ütemezése érvényes-e.

    Csak az on/off időket vizsgáljuk meg, ha nincs napkelte/napnyugta
    használatban. Hibás formátum vagy hiányzó pár esetén False-t adunk vissza.
    """

    for day in DAYS:
        data = profile.get("schedule", {}).get(day, {})
        if not data or data.get("sunrise") or data.get("sunset"):
            continue
        on = data.get("on_time")
        off = data.get("off_time")
        if bool(on) != bool(off):
            return False
        if on and off:
            try:
                dt_time.fromisoformat(on)
                dt_time.fromisoformat(off)
            except ValueError:
                return False
    return True


def check_profile_conflicts(main_app, target_name):
    """Egyszerű ütközésvizsgálat az aktivált profilok között.

    Csak az explicit on/off időket hasonlítjuk össze. A napkelte/napnyugta
    alapú beállításokat nem ellenőrizzük, mert azok pontos ideje helyfüggő.

    Args:
        main_app: Az alkalmazás fő objektuma, amely tartalmazza a profilokat.
        target_name: A vizsgálandó profil neve.

    Returns:
        List[str]: Napok és profilnevek, amelyek ütköznek a célprofillal.
    """

    target = main_app.profiles.get(target_name)
    if not target:
        return []

    def extract_intervals(profile):
        """Visszaadja a profil összes napi intervallumát.

        Az éjfélt átlépő időszakokat kettébontjuk, és a második részt a
        következő naphoz rendeljük hozzá, így a napok közötti ütközések is
        detektálhatók.
        """

        result = {day: [] for day in DAYS}
        for idx, day in enumerate(DAYS):
            data = profile.get("schedule", {}).get(day, {})
            if not data or data.get("sunrise") or data.get("sunset"):
                continue
            on = data.get("on_time")
            off = data.get("off_time")
            if not on or not off:
                continue
            try:
                on_t = dt_time.fromisoformat(on)
                off_t = dt_time.fromisoformat(off)
            except ValueError:
                continue

            start = on_t.hour * 60 + on_t.minute
            end = off_t.hour * 60 + off_t.minute

            # Ha a kikapcsolási idő korábban van, mint a bekapcsolási,
            # akkor az időszak éjfélt átlép. Azonban a pontos éjfél (00:00)
            # nem jelent átlépést, ezért csak akkor bontjuk ketté az
            # intervallumot, ha az off_time valóban kisebb, nem pedig
            # egyenlő a kezdettel.
            if end > start:
                result[day].append((start, end))
            elif end < start:
                # éjfél után ér véget -> kettéosztjuk
                result[day].append((start, 24 * 60))
                next_day = DAYS[(idx + 1) % len(DAYS)]
                result[next_day].append((0, end))
            else:
                # 0 hosszúságú intervallum, nem vesszük figyelembe
                continue
        return result

    target_intervals = extract_intervals(target)
    conflicts = []

    for other_name, other in main_app.profiles.items():
        if other_name == target_name or not other.get("active", False):
            continue
        other_intervals = extract_intervals(other)
        for day in DAYS:
            ints1 = sorted(target_intervals.get(day, []))
            ints2 = sorted(other_intervals.get(day, []))
            if not ints1 or not ints2:
                continue
            i = j = 0
            while i < len(ints1) and j < len(ints2):
                s1, e1 = ints1[i]
                s2, e2 = ints2[j]
                if s1 < e2 and s2 < e1:
                    conflicts.append(f"{day} - {other_name}")
                    break
                if e1 <= e2:
                    i += 1
                else:
                    j += 1
            if conflicts and conflicts[-1].startswith(day):
                break
    return conflicts


def save_profile(gui_widget):
    """
    Elmenti az aktuális ütemezési beállításokat JSON fájlba a GUI widgetek alapján.
    Args:
        gui_widget: A GUI2_Widget példánya.
    """
    schedule_to_save = {}
    valid = True
    for day, widgets in gui_widget.schedule_widgets.items():
        temp_data = {}
        try:
            temp_data["color"] = widgets["color"].currentText()
            if not temp_data["color"] and COLORS:
                temp_data["color"] = COLORS[0][0]

            temp_data["sunrise"] = widgets["sunrise"].isChecked()
            temp_data["sunset"] = widgets["sunset"].isChecked()

            offset_sr_str = widgets["sunrise_offset"].text()
            offset_ss_str = widgets["sunset_offset"].text()
            # Ellenőrizzük, hogy az offset szám-e
            temp_data["sunrise_offset"] = int(offset_sr_str) if offset_sr_str else 0
            temp_data["sunset_offset"] = int(offset_ss_str) if offset_ss_str else 0

            on_time_val = widgets["on_time"].currentText()
            off_time_val = widgets["off_time"].currentText()
            temp_data["on_time"] = ""
            temp_data["off_time"] = ""

            # Validáljuk a HH:MM formátumot, ha nincs napkelte/napnyugta bejelölve
            if not temp_data["sunrise"] and on_time_val:
                try:
                    dt_time.fromisoformat(on_time_val)
                    temp_data["on_time"] = on_time_val
                except ValueError:
                     raise ValueError(f"Érvénytelen bekapcsolási idő formátum: '{on_time_val}'. HH:MM formátum szükséges.")

            if not temp_data["sunset"] and off_time_val:
                 try:
                     dt_time.fromisoformat(off_time_val)
                     temp_data["off_time"] = off_time_val
                 except ValueError:
                     raise ValueError(f"Érvénytelen kikapcsolási idő formátum: '{off_time_val}'. HH:MM formátum szükséges.")

            schedule_to_save[day] = temp_data

        except ValueError as ve:
            QMessageBox.critical(gui_widget, "Hiba", f"Érvénytelen érték a '{day}' napnál: {ve}. Kérlek javítsd (idő HH:MM, offset egész szám).")
            valid = False
            break
        except Exception as e:
            QMessageBox.critical(gui_widget, "Hiba", f"Váratlan hiba a '{day}' nap feldolgozásakor: {e}")
            valid = False
            break

    if not valid:
        return

    try:
        profile_name = getattr(gui_widget, "current_profile_name", None)
        if not profile_name:
            QMessageBox.critical(gui_widget, "Hiba", "Nincs kiválasztott profil a mentéshez.")
            return

        gui_widget.main_app.profiles[profile_name]["schedule"] = schedule_to_save
        if _save_profiles_to_file(gui_widget.main_app):
            QMessageBox.information(gui_widget, "Mentés sikeres", "Az ütemezés sikeresen elmentve.")
            gui_widget.main_app.schedule = schedule_to_save
            gui_widget.unsaved_changes = False
        else:
            QMessageBox.critical(gui_widget, "Mentési hiba", "Nem sikerült a profilok mentése.")
    except Exception as e:
        QMessageBox.critical(gui_widget, "Mentési hiba", f"Hiba történt a mentés során: {e}")



def check_profiles(gui_widget):
    """Aktív ütemezési profilok ellenőrzése és LED vezérlése."""
    now_local = datetime.now(LOCAL_TZ)
    today_name_hu = DAYS_HU.get(now_local.strftime('%A'), now_local.strftime('%A'))

    main_app = gui_widget.main_app
    desired_hex = None

    try:
        for name, prof in main_app.profiles.items():
            if not prof.get("active", False):
                continue

            day_data = prof.get("schedule", {}).get(today_name_hu)
            if not day_data:
                continue

            on_time_dt = None
            off_time_dt = None

            if day_data.get("sunrise"):
                try:
                    offset = int(day_data.get("sunrise_offset", 0))
                    if main_app.sunrise:
                        on_time_dt = main_app.sunrise + timedelta(minutes=offset)
                except (ValueError, TypeError):
                    pass
            else:
                on_str = day_data.get("on_time")
                if on_str:
                    try:
                        time_obj = dt_time.fromisoformat(on_str)
                        on_time_dt = LOCAL_TZ.localize(datetime.combine(now_local.date(), time_obj))
                    except ValueError:
                        pass

            if day_data.get("sunset"):
                try:
                    offset = int(day_data.get("sunset_offset", 0))
                    if main_app.sunset:
                        off_time_dt = main_app.sunset + timedelta(minutes=offset)
                except (ValueError, TypeError):
                    pass
            else:
                off_str = day_data.get("off_time")
                if off_str:
                    try:
                        time_obj = dt_time.fromisoformat(off_str)
                        off_time_dt = LOCAL_TZ.localize(datetime.combine(now_local.date(), time_obj))
                        if on_time_dt and off_time_dt <= on_time_dt:
                            off_time_dt += timedelta(days=1)
                    except ValueError:
                        pass

            if on_time_dt and off_time_dt:
                target_color_name = day_data.get("color", "")
                target_color_hex = next((c[2] for c in COLORS if c[0] == target_color_name), None)
                if not target_color_hex:
                    continue
                if on_time_dt <= now_local < off_time_dt:
                    desired_hex = target_color_hex
                    break

        if desired_hex:
            if not main_app.is_led_on or main_app.last_color_hex != desired_hex:
                if gui_widget.controls_widget:
                    gui_widget.controls_widget.send_color_command(desired_hex)
        else:
            if main_app.is_led_on and gui_widget.controls_widget:
                gui_widget.controls_widget.turn_off_led()

    except Exception as e:
        print(f"Váratlan hiba a profilok ellenőrzésekor: {e}")
        traceback.print_exc()
