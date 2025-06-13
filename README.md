# LEDApp

LEDApp is a graphical utility for scheduling and controlling a Bluetooth LED light. It discovers the bulb using Bleak and lets you set colors and timers through a PySide6 interface. The configuration files are stored in your user profile so the app can remember the last connected device and the lighting schedule.

## Requirements

- Python 3.11 or newer
- [PySide6](https://pypi.org/project/PySide6/)
- [bleak](https://pypi.org/project/bleak/)
- requests
- suntime
- pytz

Your system also needs functional Bluetooth hardware and drivers so the application can scan and connect to the bulb.

Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Running

Launch the program by executing `python main.py` from the repository root. On Windows you can also use `start.bat` or build an executable with the provided batch files.

```bash
python main.py
```

## License

This project is released under the terms of the MIT License. See [`LICENSE`](LICENSE) for full details.
