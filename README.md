# Stibnite Shuttle

Full-colour Python 3 neon needle-shaft arcade for ElbowOS.

Steer a silver shuttle down a graphite mine shaft. Steel-grey stibnite needles close from both walls. Thread the gap, scoop the amber ore hex, keep the combo. Scrape a tip and the streak breaks.

This is an original arcade toy. It is not a commercial emulator and it does not ship ROMs.

Featured account: https://x.com/ElbowOS

Drive reel: https://drive.google.com/file/d/1XVb0BA5yoWn7yQsj3xHaMy-JQEJ3zP2S/view

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 stibnite_shuttle.py --play
```

A / D or arrow keys steer. R restarts.

## Record a 9:16 reel

```bash
python3 stibnite_shuttle.py --record
```

Headless path uses `SDL_VIDEODRIVER=dummy`, draws a 1080x1920 surface, and pipes 15 seconds at 30 fps to ffmpeg (libx264, yuv420p, CRF 20, +faststart).

Override the output path with `ELBOWOS_MP4`.
