#!/usr/bin/env python3
"""
sample_queue.py — emit the same command stream the 6502 program in
draw_scene.erl writes to $C100+.

Produces queue.json for queue_renderer.py.
"""

import json
from pathlib import Path

def table():
    t = [
        # SET_COLOR ink, CLEAR
        0x01, 0x0E, 0x10, 0x0E,
        0x04,
        # brass frame outline
        0x01, 0xD4, 0xA2, 0x4C,
        0x09, 20, 20, 280, 200,
        # inner panel
        0x01, 0x17, 0x1C, 0x17,
        0x02, 30, 40, 260, 160,
        # neon circles
        0x01, 0xD4, 0xA2, 0x4C,
        0x08, 80, 100, 18,          # FILL_CIRCLE
        0x07, 240, 100, 22,         # CIRCLE
        # cross
        0x0A, 40, 130, 240,         # HLINE
        0x0B, 160, 50, 140,         # VLINE
        # title
        0x01, 0xE8, 0xE6, 0xDC,
        0x05, 50, 160, 16,
    ]
    t += list(b"SOVEREIGN CIRCUIT")
    t += [0x05, 110, 175, 6]
    t += list(b"FABRIC")
    t += [0xFF]
    return t

def main():
    q = []
    addr = 0xC100
    for b in table():
        q.append([addr, b & 0xFF])
        addr += 1
    Path("queue.json").write_text(json.dumps(q, indent=2))
    print(f"wrote queue.json ({len(q)} bytes)")

if __name__ == "__main__":
    main()
