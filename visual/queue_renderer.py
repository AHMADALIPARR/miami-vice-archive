#!/usr/bin/env python3
"""
queue_renderer.py — software host for the Stage-1 GPU command queue.

Consumes the ordered list of {address, byte} writes that mv6502 captures
from $C100–$CFFF and turns them into framebuffer PNGs + an optional WAV.

Command vocabulary (sequential; absolute addresses ignored, write order matters):

  0x01 SET_COLOR     r g b
  0x02 FILL_RECT     x y w h
  0x03 DRAW_LINE     x1 y1 x2 y2
  0x04 CLEAR         (uses current color)
  0x05 TEXT          x y len …ascii…
  0x06 PLOT          x y
  0x07 CIRCLE        x y r
  0x08 FILL_CIRCLE   x y r
  0x09 RECT_OUTLINE  x y w h
  0x0A HLINE         x y w
  0x0B VLINE         x y h
  0x0C SET_ORIGIN    ox oy
  0x0D DEFINE_SPRITE id w h …palette-index pixels…   (0 = transparent)
  0x0E DRAW_SPRITE   id x y
  0x0F BLIT          x y w h …palette-index pixels…
  0x10 TONE          freq_lo freq_hi dur_ms          (square wave)
  0x11 NOISE         dur_ms                          (white noise)
  0xFF PRESENT                                     (flush current frame PNG)

Multiple PRESENT opcodes produce frame.png, frame-2.png, frame-3.png, …
Sound events are collected and written to sound.wav (8-bit mono, 8000 Hz).

Palette:
  0 transparent  1 brass  2 paper  3 ink
  4 neon         5 cyan   6 panel  7 white

Canvas 320×240. Coordinates 8-bit.
"""

import json
import sys
import wave
import math
import random
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

W, H = 320, 240
BG = (14, 16, 14)
BRASS = (212, 162, 76)
SAMPLE_RATE = 8000

PALETTE = {
    0: None,
    1: (212, 162, 76),
    2: (232, 230, 220),
    3: (14, 16, 14),
    4: (255, 77, 141),
    5: (77, 208, 225),
    6: (23, 28, 23),
    7: (255, 255, 255),
}

def render(queue, out_path="frame.png", sound_path="sound.wav"):
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    color = BRASS
    ox, oy = 0, 0
    sprites = {}
    sounds = []          # list of (kind, params)
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
        if op == 0x01:
            color = (next_byte(), next_byte(), next_byte())
        elif op == 0x02:
            x, y = xy(next_byte(), next_byte())
            w, h = next_byte(), next_byte()
            draw.rectangle([x, y, x + w, y + h], fill=color)
        elif op == 0x03:
            x1, y1 = xy(next_byte(), next_byte())
            x2, y2 = xy(next_byte(), next_byte())
            draw.line([x1, y1, x2, y2], fill=color, width=1)
        elif op == 0x04:
            draw.rectangle([0, 0, W, H], fill=color)
        elif op == 0x05:
            x, y = xy(next_byte(), next_byte())
            n = next_byte()
            chars = bytes(next_byte() for _ in range(n))
            text = chars.decode("ascii", errors="replace")
            draw.text((x, y), text, fill=color)
        elif op == 0x06:
            x, y = xy(next_byte(), next_byte())
            draw.point((x, y), fill=color)
        elif op == 0x07:
            x, y = xy(next_byte(), next_byte())
            r = next_byte()
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color)
        elif op == 0x08:
            x, y = xy(next_byte(), next_byte())
            r = next_byte()
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        elif op == 0x09:
            x, y = xy(next_byte(), next_byte())
            w, h = next_byte(), next_byte()
            draw.rectangle([x, y, x + w, y + h], outline=color)
        elif op == 0x0A:
            x, y = xy(next_byte(), next_byte())
            w = next_byte()
            draw.line([x, y, x + w, y], fill=color, width=1)
        elif op == 0x0B:
            x, y = xy(next_byte(), next_byte())
            h = next_byte()
            draw.line([x, y, x, y + h], fill=color, width=1)
        elif op == 0x0C:
            ox, oy = next_byte(), next_byte()
        elif op == 0x0D:
            sid = next_byte()
            sw, sh = next_byte(), next_byte()
            pixels = [next_byte() for _ in range(sw * sh)]
            sprites[sid] = (sw, sh, pixels)
        elif op == 0x0E:
            sid = next_byte()
            sx, sy = next_byte(), next_byte()
            if sid in sprites:
                sw, sh, pixels = sprites[sid]
                blit_pixels(sx, sy, sw, sh, pixels)
        elif op == 0x0F:
            bx, by = next_byte(), next_byte()
            bw, bh = next_byte(), next_byte()
            pixels = [next_byte() for _ in range(bw * bh)]
            blit_pixels(bx, by, bw, bh, pixels)
        elif op == 0x10:  # TONE freq_lo freq_hi dur_ms
            flo, fhi = next_byte(), next_byte()
            dur = next_byte()
            freq = flo | (fhi << 8)
            sounds.append(("tone", freq, dur))
        elif op == 0x11:  # NOISE dur_ms
            dur = next_byte()
            sounds.append(("noise", dur))
        elif op == 0xFF:
            frames += 1
            path = out_path if frames == 1 else out_path.replace(".png", f"-{frames}.png")
            im.save(path)
            print(f"wrote {path}")
        else:
            pass

    if frames == 0:
        im.save(out_path)
        print(f"wrote {out_path} (implicit present)")

    if sounds:
        write_wav(sounds, sound_path)
        print(f"wrote {sound_path} ({len(sounds)} events)")

    return im

def write_wav(events, path):
    """8-bit mono WAV at SAMPLE_RATE. Events are sequential."""
    samples = []
    for ev in events:
        if ev[0] == "tone":
            _, freq, dur_ms = ev
            n = max(1, int(SAMPLE_RATE * dur_ms / 1000))
            if freq <= 0:
                samples.extend([128] * n)
                continue
            period = SAMPLE_RATE / freq
            for i in range(n):
                # square wave
                phase = (i % period) / period
                v = 200 if phase < 0.5 else 56
                samples.append(v)
        elif ev[0] == "noise":
            _, dur_ms = ev
            n = max(1, int(SAMPLE_RATE * dur_ms / 1000))
            samples.extend(random.randint(40, 216) for _ in range(n))
    # clamp
    samples = [max(0, min(255, s)) for s in samples]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(samples))

def main():
    if len(sys.argv) < 2:
        print("usage: queue_renderer.py queue.json [out.png] [sound.wav]", file=sys.stderr)
        sys.exit(1)
    qpath = Path(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "frame.png"
    sound = sys.argv[3] if len(sys.argv) > 3 else "sound.wav"
    queue = json.loads(qpath.read_text())
    render(queue, out, sound)

if __name__ == "__main__":
    main()
