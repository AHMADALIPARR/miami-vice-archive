#!/usr/bin/env python3
"""
queue_renderer.py — software host for the Stage-1 GPU command queue.

Consumes the ordered list of {address, byte} writes that mv6502 captures
from $C100–$CFFF and turns them into a framebuffer PNG.

Command vocabulary (sequential; absolute addresses ignored, write order matters):

  0x01 SET_COLOR     r g b
  0x02 FILL_RECT     x y w h
  0x03 DRAW_LINE     x1 y1 x2 y2
  0x04 CLEAR         (uses current color)
  0x05 TEXT          x y len …ascii…
  0x06 PLOT          x y
  0x07 CIRCLE        x y r          (outline)
  0x08 FILL_CIRCLE   x y r
  0x09 RECT_OUTLINE  x y w h
  0x0A HLINE         x y w
  0x0B VLINE         x y h
  0x0C SET_ORIGIN    ox oy          (added to all subsequent coords)
  0xFF PRESENT

Canvas is 320×240. Coordinates are 8-bit (0–255); values > canvas are clipped
by PIL. This is the software stand-in for the queue seam the later Vulkan
host will implement.
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

W, H = 320, 240
BG = (14, 16, 14)
BRASS = (212, 162, 76)

def render(queue, out_path="frame.png"):
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    color = BRASS
    ox, oy = 0, 0
    i = 0
    frames = 0

    def next_byte():
        nonlocal i
        if i >= len(queue):
            return 0
        _, b = queue[i]
        i += 1
        return b

    def xy(x, y):
        return (x + ox) & 0xFF, (y + oy) & 0xFF

    while i < len(queue):
        op = next_byte()
        if op == 0x01:  # SET_COLOR
            color = (next_byte(), next_byte(), next_byte())
        elif op == 0x02:  # FILL_RECT
            x, y = xy(next_byte(), next_byte())
            w, h = next_byte(), next_byte()
            draw.rectangle([x, y, x + w, y + h], fill=color)
        elif op == 0x03:  # DRAW_LINE
            x1, y1 = xy(next_byte(), next_byte())
            x2, y2 = xy(next_byte(), next_byte())
            draw.line([x1, y1, x2, y2], fill=color, width=1)
        elif op == 0x04:  # CLEAR
            draw.rectangle([0, 0, W, H], fill=color)
        elif op == 0x05:  # TEXT
            x, y = xy(next_byte(), next_byte())
            n = next_byte()
            chars = bytes(next_byte() for _ in range(n))
            text = chars.decode("ascii", errors="replace")
            draw.text((x, y), text, fill=color)
        elif op == 0x06:  # PLOT
            x, y = xy(next_byte(), next_byte())
            draw.point((x, y), fill=color)
        elif op == 0x07:  # CIRCLE outline
            x, y = xy(next_byte(), next_byte())
            r = next_byte()
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color)
        elif op == 0x08:  # FILL_CIRCLE
            x, y = xy(next_byte(), next_byte())
            r = next_byte()
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        elif op == 0x09:  # RECT_OUTLINE
            x, y = xy(next_byte(), next_byte())
            w, h = next_byte(), next_byte()
            draw.rectangle([x, y, x + w, y + h], outline=color)
        elif op == 0x0A:  # HLINE
            x, y = xy(next_byte(), next_byte())
            w = next_byte()
            draw.line([x, y, x + w, y], fill=color, width=1)
        elif op == 0x0B:  # VLINE
            x, y = xy(next_byte(), next_byte())
            h = next_byte()
            draw.line([x, y, x, y + h], fill=color, width=1)
        elif op == 0x0C:  # SET_ORIGIN
            ox, oy = next_byte(), next_byte()
        elif op == 0xFF:  # PRESENT
            frames += 1
            path = out_path if frames == 1 else out_path.replace(".png", f"-{frames}.png")
            im.save(path)
            print(f"wrote {path}")
        else:
            pass  # unknown opcode: skip

    if frames == 0:
        im.save(out_path)
        print(f"wrote {out_path} (implicit present)")
    return im

def main():
    if len(sys.argv) < 2:
        print("usage: queue_renderer.py queue.json [out.png]", file=sys.stderr)
        sys.exit(1)
    qpath = Path(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "frame.png"
    queue = json.loads(qpath.read_text())
    render(queue, out)

if __name__ == "__main__":
    main()
