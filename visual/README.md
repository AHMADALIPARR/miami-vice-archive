# Visual layer (software host for the GPU queue)

Stage 1 already captures every write to `$C100–$CFFF` as an ordered
`{address, byte}` list (`mv6502:gpu_queue/1`). This directory is the
first host that consumes that list and produces a framebuffer.

## Command vocabulary

Sequential opcodes (absolute addresses ignored; only write order matters):

| Opcode | Name          | Operands     | Effect |
|--------|---------------|--------------|--------|
| `0x01` | SET_COLOR     | r g b        | current color |
| `0x02` | FILL_RECT     | x y w h      | filled rectangle |
| `0x03` | DRAW_LINE     | x1 y1 x2 y2  | line |
| `0x04` | CLEAR         | —            | fill canvas with current color |
| `0x05` | TEXT          | x y len …    | ASCII text |
| `0x06` | PLOT          | x y          | single pixel |
| `0x07` | CIRCLE        | x y r        | outline circle |
| `0x08` | FILL_CIRCLE   | x y r        | filled circle |
| `0x09` | RECT_OUTLINE  | x y w h      | rectangle outline |
| `0x0A` | HLINE         | x y w        | horizontal line |
| `0x0B` | VLINE         | x y h        | vertical line |
| `0x0C` | SET_ORIGIN    | ox oy        | offset added to later coordinates |
| `0xFF` | PRESENT       | —            | flush PNG |

Canvas is 320×240. Coordinates are 8-bit.

## 6502 program

`draw_scene.erl` exports `terms/0` — a list of `mv_asm` terms. It copies
a byte table to consecutive addresses starting at `$C100`. Every `STA`
into the queue window is captured by the runtime.

```erlang
{ok, Bin, _} = mv_asm:assemble(draw_scene:terms(), 16#0200),
{ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
Queue = mv6502:gpu_queue(M).
```

Dump `Queue` as JSON `[[addr,byte],...]` and feed it to the renderer.

## Software path (no Erlang required)

```bash
cd visual
python3 sample_queue.py                 # same bytes the 6502 program emits
python3 queue_renderer.py queue.json frame.png
```

Requires Pillow.

This is the software stand-in for the queue seam. The real Vulkan host
(Stage 6, owner’s carve, separate repo) implements the same opcodes.
