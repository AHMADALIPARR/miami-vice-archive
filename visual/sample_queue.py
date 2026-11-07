#!/usr/bin/env python3
"""
sample_queue.py — emit a Miami-Vice-flavored command stream that the
Stage-1 runtime would produce by writing to $C100+.

Produces queue.json that queue_renderer.py turns into a PNG.
"""

import json
from pathlib import Path

def emit():
    q = []
    addr = 0xC100

    def w(b):
        nonlocal addr
        q.append([addr, b & 0xFF])
        addr += 1

    # clear to near-black
    w(0x01); w(0x0e); w(0x10); w(0x0e)
    w(0x04)

    # brass frame
    w(0x01); w(0xd4); w(0xa2); w(0x4c)
    w(0x02); w(20); w(20); w(280); w(200)

    # inner paper panel
    w(0x01); w(0x17); w(0x1c); w(0x17)
    w(0x02); w(30); w(40); w(260); w(160)

    # neon accent line
    w(0x01); w(0xd4); w(0xa2); w(0x4c)
    w(0x03); w(40); w(60); w(280); w(60)

    # title text
    w(0x01); w(0xe8); w(0xe6); w(0xdc)
    text = b"SOVEREIGN CIRCUIT"
    w(0x05); w(50); w(90); w(len(text))
    for c in text:
        w(c)

    text2 = b"FABRIC"
    w(0x05); w(110); w(110); w(len(text2))
    for c in text2:
        w(c)

    # present
    w(0xFF)

    Path("queue.json").write_text(json.dumps(q, indent=2))
    print(f"wrote queue.json ({len(q)} commands)")

if __name__ == "__main__":
    emit()
