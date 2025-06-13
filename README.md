# LEDApp

LEDApp is a desktop application for controlling LED lights. It uses PySide6 for the user interface.

## Installing dependencies

Install the Python dependencies with `pip`:

```bash
pip install -r requirements.txt
```

PySide6 depends on the Qt runtime libraries. If these are missing you may encounter errors such as missing `libEGL.so` or "Qt platform plugin could not be initialized".

### Linux

Use your package manager to install the Qt libraries. On Debian or Ubuntu based systems the following packages resolve most missing Qt library errors:

```bash
sudo apt-get install libegl1 libqt6gui6 libqt6network6 libxkbcommon-x11-0 libglib2.0-0
```

You may also need additional packages from the `qt6-base` or `mesa` groups depending on your distribution.

### Windows

The PySide6 wheel bundles the necessary Qt libraries. If you see DLL errors, reinstall PySide6:

```batch
python -m pip install --force-reinstall PySide6
```

Ensure that the Microsoft Visual C++ Redistributable is installed because Qt relies on it.

## Running

Run the application from the repository root:

```bash
python main.py
```
