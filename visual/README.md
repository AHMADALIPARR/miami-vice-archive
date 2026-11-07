# Visual layer (software host for the GPU queue)

Stage 1 already captures every write to `$C100–$CFFF` as an ordered
`{address, byte}` list (`mv6502:gpu_queue/1`). This directory is the
first host that consumes that list and produces framebuffer PNGs and
an optional WAV.

## Command vocabulary

Sequential opcodes (absolute addresses ignored; only write order matters):

| Opcode | Name          | Operands                          | Effect |
|--------|---------------|-----------------------------------|--------|
| `0x01` | SET_COLOR     | r g b                             | current color |
| `0x02` | FILL_RECT     | x y w h                           | filled rectangle |
| `0x03` | DRAW_LINE     | x1 y1 x2 y2                       | line |
| `0x04` | CLEAR         | —                                 | fill canvas with current color |
| `0x05` | TEXT          | x y len …                         | ASCII text |
| `0x06` | PLOT          | x y                               | single pixel |
| `0x07` | CIRCLE        | x y r                             | outline circle |
| `0x08` | FILL_CIRCLE   | x y r                             | filled circle |
| `0x09` | RECT_OUTLINE  | x y w h                           | rectangle outline |
| `0x0A` | HLINE         | x y w                             | horizontal line |
| `0x0B` | VLINE         | x y h                             | vertical line |
| `0x0C` | SET_ORIGIN    | ox oy                             | offset added to later coordinates |
| `0x0D` | DEFINE_SPRITE | id w h …pixels…                   | store sprite (palette indices) |
| `0x0E` | DRAW_SPRITE   | id x y                            | blit stored sprite |
| `0x0F` | BLIT          | x y w h …pixels…                  | immediate palette-index blit |
| `0x10` | TONE          | freq_lo freq_hi dur_ms            | square-wave tone |
| `0x11` | NOISE         | dur_ms                            | white noise |
| `0xFF` | PRESENT       | —                                 | flush PNG (multiple = animation) |

### Palette

| Index | Color | RGB |
|-------|-------|-----|
| 0 | transparent | — |
| 1 | brass | `#d4a24c` |
| 2 | paper | `#e8e6dc` |
| 3 | ink | `#0e100e` |
| 4 | neon | `#ff4d8d` |
| 5 | cyan | `#4dd0e1` |
| 6 | panel | `#171c17` |
| 7 | white | `#ffffff` |

Canvas is 320×240. Coordinates are 8-bit.

## Animation

Each `0xFF` PRESENT flushes the current canvas to a PNG. The first is
`frame.png`; subsequent ones are `frame-2.png`, `frame-3.png`, etc.
The sample emits four frames: a pulsing circle, a sprite that steps
right, and a rising tone.

## Sound

`0x10` and `0x11` are collected in order and written to `sound.wav`
(8-bit mono, 8000 Hz). Events play sequentially.

## 6502 program

`draw_scene.erl` exports `terms/0`. It copies a 4-frame command table
(including DEFINE_SPRITE, DRAW_SPRITE, TONE, NOISE, and PRESENT) to
`$C100+`.

```erlang
{ok, Bin, _} = mv_asm:assemble(draw_scene:terms(), 16#0200),
{ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
Queue = mv6502:gpu_queue(M).
```

## Software path

```bash
cd visual
python3 sample_queue.py
python3 queue_renderer.py queue.json frame.png sound.wav
```

Produces `frame.png`, `frame-2.png`, `frame-3.png`, `frame-4.png`, and
`sound.wav`. Requires Pillow (stdlib `wave` for audio).

This is the software stand-in for the queue seam. The real Vulkan host
(Stage 6) implements the same opcodes.
