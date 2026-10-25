# Vanta City

A native desktop game built with Pygame. Explore a top-down open city, cruise in your car, collect cash, and take contracts to build your reputation. It runs as a windowed game; it is not a website.

## Run the game

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python vanta_city_game.py
```

Press **Enter** on the title screen to play.

## Controls

- **WASD**: walk or drive
- **E** or **Space**: enter or exit your car
- **Shift**: boost while driving
- **Tab**: open contracts; press **1–5** to accept one
- **Esc**: pause or resume
- **F5**: save
- **N**: start a new profile from the pause screen

Progress saves to `~/.vanta_city_save.json`.

## ATM demo

The original PyQt ATM project is still included. Launch it with `python "atm_in _python.py"`.
