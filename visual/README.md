# Visual layer (software host for the GPU queue)

Stage 1 already captures every write to `$C100–$CFFF` as an ordered
`{address, byte}` list (`mv6502:gpu_queue/1`). This directory is the
first host that consumes that list and produces a framebuffer.

## Command vocabulary

Sequential opcodes starting at the first write:

| Opcode | Name       | Operands                  | Effect |
|--------|------------|---------------------------|--------|
| `0x01` | SET_COLOR  | r g b                     | current color |
| `0x02` | FILL_RECT  | x y w h                   | filled rectangle (8-bit coords, 320×240) |
| `0x03` | DRAW_LINE  | x1 y1 x2 y2               | line |
| `0x04` | CLEAR      | —                         | fill canvas with current color |
| `0x05` | TEXT       | x y len …                 | ASCII text |
| `0xFF` | PRESENT    | —                         | flush PNG |

Absolute addresses are ignored; only write order matters. A later
Vulkan host implements the same opcodes.

## Run

```bash
cd visual
python3 sample_queue.py          # writes queue.json
python3 queue_renderer.py queue.json frame.png
```

Requires Pillow (`pip install Pillow`).

This is the software stand-in for the queue seam. The real Vulkan
host (Stage 6, owner’s carve, separate repo) replaces the PIL backend
with device-side pipelines while keeping the same command contract.
