# Visual layer (software host for the GPU queue)

Stage 1 already captures every write to `$C100–$CFFF` as an ordered
`{address, byte}` list (`mv6502:gpu_queue/1`). This directory is the
first host that consumes that list and produces a framebuffer.

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
| `0xFF` | PRESENT       | —                                 | flush PNG |

### Palette (index → color)

| Index | Color   | RGB |
|-------|---------|-----|
| 0     | transparent | — |
| 1     | brass   | `#d4a24c` |
| 2     | paper   | `#e8e6dc` |
| 3     | ink     | `#0e100e` |
| 4     | neon    | `#ff4d8d` |
| 5     | cyan    | `#4dd0e1` |
| 6     | panel   | `#171c17` |
| 7     | white   | `#ffffff` |

Canvas is 320×240. Coordinates are 8-bit. Sprite/blit pixels are palette indices; 0 is skipped.

## 6502 program

`draw_scene.erl` exports `terms/0`. It copies a command table (including a DEFINE_SPRITE of an 8×8 diamond and several DRAW_SPRITE / BLIT calls) to `$C100+`.

```erlang
{ok, Bin, _} = mv_asm:assemble(draw_scene:terms(), 16#0200),
{ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
Queue = mv6502:gpu_queue(M).
```

## Software path

```bash
cd visual
python3 sample_queue.py
python3 queue_renderer.py queue.json frame.png
```

Requires Pillow.

This is the software stand-in for the queue seam. The real Vulkan host
(Stage 6) implements the same opcodes.
