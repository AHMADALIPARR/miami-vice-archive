#!/usr/bin/env python3
"""
sample_queue.py — emit an animated command stream (4 frames) plus tones
that the 6502 program in draw_scene.erl would write to $C100+.
"""

import json
from pathlib import Path

SPRITE = [
    0,0,0,1,1,0,0,0,
    0,0,1,4,4,1,0,0,
    0,1,4,2,2,4,1,0,
    1,4,2,7,7,2,4,1,
    1,4,2,7,7,2,4,1,
    0,1,4,2,2,4,1,0,
    0,0,1,4,4,1,0,0,
    0,0,0,1,1,0,0,0,
]

def frame_bytes(n, sprite_x):
    """Commands for one frame. n is 0..3 for slight variation."""
    t = [
        # clear
        0x01, 0x0E, 0x10, 0x0E,
        0x04,
        # frame
        0x01, 0xD4, 0xA2, 0x4C,
        0x09, 20, 20, 280, 200,
        # panel
        0x01, 0x17, 0x1C, 0x17,
        0x02, 30, 40, 260, 160,
        # pulsing circle (radius grows)
        0x01, 0xD4, 0xA2, 0x4C,
        0x08, 80, 100, 14 + n * 2,
        # moving sprite
        0x0D, 1, 8, 8,
    ]
    t += SPRITE
    t += [0x0E, 1, sprite_x, 90]
    # title only on last frame
    if n == 3:
        t += [
            0x01, 0xE8, 0xE6, 0xDC,
            0x05, 50, 160, 16,
        ]
        t += list(b"SOVEREIGN CIRCUIT")
    # tone that rises
    freq = 220 + n * 110
    t += [0x10, freq & 0xFF, (freq >> 8) & 0xFF, 120]
    if n == 2:
        t += [0x11, 40]  # short noise
    t += [0xFF]  # present this frame
    return t

def table():
    t = []
    for n in range(4):
        t += frame_bytes(n, 40 + n * 40)
    return t

def main():
    q = []
    addr = 0xC100
    for b in table():
        q.append([addr, b & 0xFF])
        addr += 1
    Path("queue.json").write_text(json.dumps(q, indent=2))
    print(f"wrote queue.json ({len(q)} bytes, 4 frames)")

if __name__ == "__main__":
    main()
