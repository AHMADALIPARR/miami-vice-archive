#!/usr/bin/env python3
"""
queue_renderer.py — software host for the Stage-1 GPU command queue.

Consumes the ordered list of {address, byte} writes that mv6502 captures
from $C100–$CFFF and turns them into a framebuffer PNG.

Command vocabulary (sequential, little-endian where multi-byte):

  $C100: opcode
  following addresses: operands

Opcodes:
  0x01 SET_COLOR   r g b          (3 bytes)
  0x02 FILL_RECT   x y w h        (4 bytes, 8-bit coords, 320x240 canvas)
  0x03 DRAW_LINE   x1 y1 x2 y2    (4 bytes)
  0x04 CLEAR                      (no operands; uses current color)
  0x05 TEXT        x y len ...    (len bytes of ASCII)
  0xFF PRESENT                    (flush current frame; optional name follows as length-prefixed)

The host ignores the absolute address and only cares about write order.
This is the same contract the later Vulkan host will implement.
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

W, H = 320, 240
BG = (14, 16, 14)          # ink from brand notes
BRASS = (212, 162, 76)
PAPER = (232, 230, 220)

def render(queue, out_path="frame.png"):
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    color = BRASS
    i = 0
    frames = 0

    def next_byte():
        nonlocal i
        if i >= len(queue):
            return 0
        _, b = queue[i]
        i += 1
        return b

    while i < len(queue):
        op = next_byte()
        if op == 0x01:  # SET_COLOR
            r, g, b = next_byte(), next_byte(), next_byte()
            color = (r, g, b)
        elif op == 0x02:  # FILL_RECT
            x, y, w, h = next_byte(), next_byte(), next_byte(), next_byte()
            draw.rectangle([x, y, x + w, y + h], fill=color)
        elif op == 0x03:  # DRAW_LINE
            x1, y1, x2, y2 = next_byte(), next_byte(), next_byte(), next_byte()
            draw.line([x1, y1, x2, y2], fill=color, width=1)
        elif op == 0x04:  # CLEAR
            draw.rectangle([0, 0, W, H], fill=color)
        elif op == 0x05:  # TEXT
            x, y, n = next_byte(), next_byte(), next_byte()
            chars = bytes(next_byte() for _ in range(n))
            try:
                text = chars.decode("ascii", errors="replace")
            except Exception:
                text = "?"
            draw.text((x, y), text, fill=color)
        elif op == 0xFF:  # PRESENT
            frames += 1
            path = out_path if frames == 1 else out_path.replace(".png", f"-{frames}.png")
            im.save(path)
            print(f"wrote {path}")
        else:
            # unknown: skip
            pass

    if frames == 0:
        im.save(out_path)
        print(f"wrote {out_path} (implicit present)")
    return im

def main():
    if len(sys.argv) < 2:
        print("usage: queue_renderer.py queue.json [out.png]", file=sys.stderr)
        print("  queue.json = [[addr, byte], ...]", file=sys.stderr)
        sys.exit(1)
    qpath = Path(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "frame.png"
    queue = json.loads(qpath.read_text())
    render(queue, out)

if __name__ == "__main__":
    main()
