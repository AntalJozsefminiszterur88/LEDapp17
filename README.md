# LEDApp

LEDApp ("LED-Irányító 2000") is a desktop application for controlling Bluetooth LED strips. The program lets you connect to a BLE light controller and define color schedules for every day of the week.

## Installation

1. Install **Python 3.9** or later.
2. Clone this repository.
3. Install the dependencies:
   ```bash
   pip install PySide6 bleak requests suntime pytz tzlocal
   ```

## Running

Execute the application from the repository root:

```bash
python main.py
```

Use `--tray` to start the app minimized to the system tray:

```bash
python main.py --tray
```

Windows users can also launch `start.bat`.

## Basic Usage

Upon start the app scans for nearby BLE devices. Select your LED controller from the list to connect. The second screen lets you set colors, brightness and scheduling rules for each day. Settings are saved to `led_settings.json` and `led_schedule.json` in your Documents folder.

## Dependencies

- [PySide6](https://pyside.org) – GUI framework
- [bleak](https://github.com/hbldh/bleak) – Bluetooth Low Energy library
- [requests](https://docs.python-requests.org) – HTTP requests for location lookup
- [suntime](https://github.com/SatAgro/suntime) – sunrise and sunset calculations
- [pytz](https://pypi.org/project/pytz/) – timezone utilities
- [tzlocal](https://pypi.org/project/tzlocal/) – determines the local timezone (optional)

---

# LEDApp (Magyarul)

A LEDApp ("LED-Irányító 2000") asztali alkalmazás Bluetooth LED szalagok vezérlésére. Segítségével csatlakozhatsz BLE fényforrásodhoz, és minden napra egyedi színidőzítést állíthatsz be.

## Telepítés

1. Telepíts legalább **Python 3.9**-et.
2. Klónozd a projektet.
3. Telepítsd a függőségeket:
   ```bash
   pip install PySide6 bleak requests suntime pytz tzlocal
   ```

## Futtatás

A programot a könyvtár gyökeréből indíthatod:

```bash
python main.py
```

A `--tray` kapcsolóval rendszertálcára minimalizálva indul:

```bash
python main.py --tray
```

Windowson futtathatod a `start.bat` fájlt is.

## Alap használat

Indítás után a program felderíti a közeli BLE eszközöket. Válaszd ki a listából a LED vezérlőt. A második képernyőn színeket, fényerőt és hétköznapi szabályokat állíthatsz be. A beállítások a `led_settings.json` és `led_schedule.json` fájlokba kerülnek a Dokumentumok mappádban.

## Függőségek

- PySide6 – grafikus felület
- bleak – Bluetooth Low Energy könyvtár
- requests – HTTP lekérések helymeghatározáshoz
- suntime – napkelte- és napnyugta-számítások
- pytz – időzóna könyvtár
- tzlocal – a helyi időzóna meghatározása (opcionális)
