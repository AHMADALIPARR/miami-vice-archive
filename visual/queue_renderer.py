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
  0x0C SET_ORIGIN    ox oy
  0x0D DEFINE_SPRITE id w h …palette-index pixels…   (0 = transparent)
  0x0E DRAW_SPRITE   id x y
  0x0F BLIT          x y w h …palette-index pixels…  (immediate, no store)
  0xFF PRESENT

Palette (index → RGB):
  0  transparent
  1  brass   #d4a24c
  2  paper   #e8e6dc
  3  ink     #0e100e
  4  neon    #ff4d8d
  5  cyan    #4dd0e1
  6  panel   #171c17
  7  white   #ffffff

Canvas is 320×240. Coordinates are 8-bit.
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

PALETTE = {
    0: None,                    # transparent
    1: (212, 162, 76),          # brass
    2: (232, 230, 220),         # paper
    3: (14, 16, 14),            # ink
    4: (255, 77, 141),           # neon
    5: (77, 208, 225),           # cyan
    6: (23, 28, 23),             # panel
    7: (255, 255, 255),          # white
}

def render(queue, out_path="frame.png"):
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    color = BRASS
    ox, oy = 0, 0
    sprites = {}          # id -> (w, h, [indices])
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

    def blit_pixels(dx, dy, w, h, pixels):
        for py in range(h):
            for px in range(w):
                idx = pixels[py * w + px]
                rgb = PALETTE.get(idx)
                if rgb is not None:
                    x, y = xy(dx + px, dy + py)
                    if 0 <= x < W and 0 <= y < H:
                        im.putpixel((x, y), rgb)

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
        elif op == 0x0D:  # DEFINE_SPRITE id w h …pixels…
            sid = next_byte()
            sw, sh = next_byte(), next_byte()
            pixels = [next_byte() for _ in range(sw * sh)]
            sprites[sid] = (sw, sh, pixels)
        elif op == 0x0E:  # DRAW_SPRITE id x y
            sid = next_byte()
            sx, sy = next_byte(), next_byte()
            if sid in sprites:
                sw, sh, pixels = sprites[sid]
                blit_pixels(sx, sy, sw, sh, pixels)
        elif op == 0x0F:  # BLIT x y w h …pixels…
            bx, by = next_byte(), next_byte()
            bw, bh = next_byte(), next_byte()
            pixels = [next_byte() for _ in range(bw * bh)]
            blit_pixels(bx, by, bw, bh, pixels)
        elif op == 0xFF:  # PRESENT
            frames += 1
            path = out_path if frames == 1 else out_path.replace(".png", f"-{frames}.png")
            im.save(path)
            print(f"wrote {path}")
        else:
            pass

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
