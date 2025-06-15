import types
import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402


def setup_pyside(monkeypatch):
    widgets = types.SimpleNamespace(
        QMessageBox=types.SimpleNamespace(
            critical=lambda *a, **k: None,
            information=lambda *a, **k: None,
        )
    )
    core = types.SimpleNamespace(Qt=object())
    pyside = types.ModuleType("PySide6")
    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", widgets)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", core)
    # minimal pytz substitute
    tz = types.SimpleNamespace(zone="UTC")
    pytz_dummy = types.SimpleNamespace(
        timezone=lambda x: types.SimpleNamespace(zone=x),
        UnknownTimeZoneError=Exception,
        utc=tz,
    )
    monkeypatch.setitem(sys.modules, "pytz", pytz_dummy)
    monkeypatch.setitem(
        sys.modules,
        "core.sun_logic",
        types.SimpleNamespace(
            get_local_sun_info=lambda *a, **k: None,
            get_hungarian_day_name=lambda x: x,
            DAYS_HU={},
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "core.location_utils",
        types.SimpleNamespace(get_sun_times=lambda *a, **k: None),
    )


def test_get_default_schedule(monkeypatch):
    setup_pyside(monkeypatch)
    glogic = importlib.import_module("gui.gui2_schedule_logic")
    schedule = glogic.get_default_schedule()
    assert set(schedule.keys()) == set(config.DAYS)
    for day in config.DAYS:
        assert set(schedule[day].keys()) == {
            "color",
            "on_time",
            "off_time",
            "sunrise",
            "sunrise_offset",
            "sunset",
            "sunset_offset",
        }


def test_check_profile_conflicts(monkeypatch):
    setup_pyside(monkeypatch)
    glogic = importlib.import_module("gui.gui2_schedule_logic")
    default = glogic.get_default_schedule()
    prof1 = {k: v.copy() for k, v in default.items()}
    prof2 = {k: v.copy() for k, v in default.items()}
    prof1["Hétfő"].update({"on_time": "08:00", "off_time": "10:00"})
    prof2["Hétfő"].update({"on_time": "09:00", "off_time": "11:00"})
    app = types.SimpleNamespace(
        profiles={
            "P1": {"active": True, "schedule": prof1},
            "P2": {"active": True, "schedule": prof2},
        }
    )
    conflicts = glogic.check_profile_conflicts(app, "P1")
    assert "Hétfő - P2" in conflicts


def test_check_profiles_cross_midnight(monkeypatch):
    """Schedule spanning midnight should activate only during its interval."""
    setup_pyside(monkeypatch)

    # Use real pytz for timezone handling
    sys.modules.pop("pytz", None)
    import pytz
    monkeypatch.setitem(sys.modules, "pytz", pytz)

    glogic = importlib.import_module("gui.gui2_schedule_logic")
    glogic = importlib.reload(glogic)

    # Hungarian day names mapping
    monkeypatch.setattr(
        glogic,
        "DAYS_HU",
        {"Monday": "Hétfő", "Tuesday": "Kedd", "Sunday": "Vasárnap"},
        raising=False,
    )
    monkeypatch.setattr(glogic, "LOCAL_TZ", pytz.timezone("Europe/Budapest"), raising=False)

    schedule = glogic.get_default_schedule()
    schedule["Hétfő"].update({"color": "Piros", "on_time": "22:00", "off_time": "02:00"})

    main_app = types.SimpleNamespace(
        profiles={"Test": {"active": True, "schedule": schedule}},
        sunrise=None,
        sunset=None,
        is_led_on=False,
        last_color_hex="",
        latitude=0.0,
        longitude=0.0,
    )

    class DummyControls:
        def __init__(self):
            self.sent = []
            self.turned_off = False

        def send_color_command(self, hex_code):
            self.sent.append(hex_code)

        def turn_off_led(self):
            self.turned_off = True

    controls = DummyControls()
    gui = types.SimpleNamespace(main_app=main_app, controls_widget=controls)

    from freezegun import freeze_time

    # 23:00 local (22:00 UTC) should trigger the color
    with freeze_time("2020-01-06 22:00:00", tz_offset=0):
        glogic.check_profiles(gui)
        assert controls.sent == [next(c[2] for c in config.COLORS if c[0] == "Piros")]

    controls.sent.clear()
    main_app.is_led_on = True

    # 03:00 local (02:00 UTC) is outside the interval
    with freeze_time("2020-01-07 02:00:00", tz_offset=0):
        glogic.check_profiles(gui)
        assert controls.sent == []
