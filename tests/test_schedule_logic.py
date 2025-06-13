import types
import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
import pytest


def setup_pyside(monkeypatch):
    widgets = types.SimpleNamespace(
        QMessageBox=types.SimpleNamespace(
            critical=lambda *a, **k: None,
            information=lambda *a, **k: None,
        )
    )
    core = types.SimpleNamespace(Qt=object())
    pyside = types.ModuleType('PySide6')
    monkeypatch.setitem(sys.modules, 'PySide6', pyside)
    monkeypatch.setitem(sys.modules, 'PySide6.QtWidgets', widgets)
    monkeypatch.setitem(sys.modules, 'PySide6.QtCore', core)
    monkeypatch.setitem(sys.modules, 'core.sun_logic', types.SimpleNamespace(
        get_local_sun_info=lambda *a, **k: None,
        get_hungarian_day_name=lambda x: x,
        DAYS_HU={}
    ))
    monkeypatch.setitem(sys.modules, 'core.location_utils', types.SimpleNamespace(
        get_sun_times=lambda *a, **k: None
    ))


def test_get_default_schedule(monkeypatch):
    setup_pyside(monkeypatch)
    glogic = importlib.import_module('gui.gui2_schedule_logic')
    schedule = glogic.get_default_schedule()
    assert set(schedule.keys()) == set(config.DAYS)
    for day in config.DAYS:
        assert set(schedule[day].keys()) == {
            'color', 'on_time', 'off_time', 'sunrise',
            'sunrise_offset', 'sunset', 'sunset_offset'
        }


def test_check_profile_conflicts(monkeypatch):
    setup_pyside(monkeypatch)
    glogic = importlib.import_module('gui.gui2_schedule_logic')
    default = glogic.get_default_schedule()
    prof1 = {k: v.copy() for k, v in default.items()}
    prof2 = {k: v.copy() for k, v in default.items()}
    prof1['Hétfő'].update({'on_time': '08:00', 'off_time': '10:00'})
    prof2['Hétfő'].update({'on_time': '09:00', 'off_time': '11:00'})
    app = types.SimpleNamespace(profiles={
        'P1': {'active': True, 'schedule': prof1},
        'P2': {'active': True, 'schedule': prof2},
    })
    conflicts = glogic.check_profile_conflicts(app, 'P1')
    assert 'Hétfő - P2' in conflicts
