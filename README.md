# Miami Vice Archive

<video width="320" height="240" controls autoplay loop muted>
  <source src="visual/animation.mp4" type="video/mp4">
</video>

**A verified 6502 container runtime that executes archived source on the memory map drawn in the poster.**

The clip above is the software visual host running today: four frames of a 320×240 canvas driven by the Stage-1 GPU command queue, with square-wave tones and a short noise burst. A 6502 program (`visual/draw_scene.erl`) writes the opcodes; `visual/queue_renderer.py` turns the ordered writes into PNGs and a WAV; ffmpeg stitches them into the MP4.

This is not a finished game. It is the execution architecture that will eventually run BASIC listings from Miami Vice Magazine (and related machine-code reconstructions). Listings enter as data, are lowered through a 6502 IR into ROPE/AGC assembly, and run inside a banked memory runtime with a declared map, an I/O port, and a GPU command queue. Compute and rendering layers sit behind it; the native host is a Jetson.

![Architecture Poster](docs/architecture-poster.jpg)

The poster is the specification. Everything below is what actually runs today.

## What runs today (Stage 1 + software visual host)

`runtime/` contains a banked 6502 virtual machine (`mv6502.erl`) and a small assembler (`mv_asm.erl`). The CPU core is the verified engine from `ace-sovereign`; the memory layer implements the poster’s map:

| Region | Purpose |
|--------|---------|
| `$0000–$00FF` | Zero page (dedicated) |
| `$0100–$01FF` | Stack (dedicated) |
| `$0200–$7FFF` | Banked program/data window (bank register at `$C000`) |
| `$8000–$BFFF` | ROPE/AGC runtime RAM (always mapped) |
| `$C000–$FFFF` | I/O + GPU command queue |
| `$C100–$CFFF` | GPU queue (writes captured as `{address, byte}`) |
| `$FE00` | Output port (bytes appear on stdout) |
| `$FFFA–$FFFF` | Vector shadow |

**Verified by execution** (`runtime/test/`, 16/16 checks):

- Arithmetic, loops, JSR/RTS, BCD, the NMOS JMP-indirect page-boundary quirk, stack, indexed-indirect, illegal-opcode halt, step budget.
- Bank isolation (same address, different banks, distinct stores).
- Bank register wraps (`7 rem 4 = 3`) and reads back.
- GPU queue captures writes in order; the queue window stores nothing.
- Zero page and runtime RAM survive bank switches.

A CLI runner (`runtime/run.sh`) takes a binary, an origin, and a step budget, writes the `$FE00` output bytes to stdout, and reports the halt reason on stderr. The “HI” program (LDA/STA to `$FE00`) produces the bytes `HI` and exits clean on `BRK`.

### Software visual host (`visual/`)

The GPU queue already exists. `visual/queue_renderer.py` consumes the ordered `{address, byte}` list and produces 320×240 PNGs plus a WAV. Multiple `PRESENT` opcodes become an animation; `TONE` / `NOISE` become the soundtrack.

Opcode set: SET_COLOR, FILL_RECT, DRAW_LINE, CLEAR, TEXT, PLOT, CIRCLE, FILL_CIRCLE, RECT_OUTLINE, HLINE, VLINE, SET_ORIGIN, DEFINE_SPRITE, DRAW_SPRITE, BLIT, TONE, NOISE, PRESENT.

`visual/draw_scene.erl` is a 6502 program (mv_asm terms) that copies a 4-frame command table to `$C100+`. Every STA into the queue window is captured by the runtime. `visual/sample_queue.py` emits the identical byte stream so the frames can be rendered without Erlang.

```bash
cd visual
python3 sample_queue.py
python3 queue_renderer.py queue.json frame.png sound.wav
# then the ffmpeg command in visual/README.md to rebuild animation.mp4
```

To run the real 6502 program:

```erlang
{ok, Bin, _} = mv_asm:assemble(draw_scene:terms(), 16#0200),
{ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
Queue = mv6502:gpu_queue(M).
```

This is the software stand-in for the queue seam. The real Vulkan host remains Stage 6 (owner’s carve, separate repo).

## What does not run yet

- No Miami Vice Magazine BASIC listing has been ingested.
- No PureBasic parser, no 6502-to-ROPE/AGC lowering, no AGC assembler for the corpus.
- No real Vulkan device, SPIR-V, or unified-memory buffer ownership. The software renderer is a host-side interpreter of the same command contract the Vulkan host will implement.
- There is still no full game binary; the sample animation is a command-stream demo.

## Pipeline (the poster’s top strip)

```
PureBasic (magazine listings)
    ↓
6502 IR
    ↓
ROPE / AGC assembly
    ↓
Container & memory runtime  ← you are here (Stage 1, verified)
    ↓
software queue renderer     ← visual host (this tree)
    ↓
Pascal / Fortran compute
    ↓
Vulkan render (Stage 6)
```

## Documents

- [BLUEPRINT.md](BLUEPRINT.md) — component map, what exists, stage plan 1–6
- [STATUS.md](STATUS.md) — verified facts vs. staged work
- [AGENTS.md](AGENTS.md) — repository laws (verify before commit, provenance, claims match execution)
- [LICENSE](LICENSE) — sovereign license
- [visual/README.md](visual/README.md) — command vocabulary, 6502 program, animation, sound, and how to rebuild the video

## Related

- [6502-transformer](https://github.com/AHMADALIPARR/6502-transformer) — 6502 and AGC corpora
- [ace-sovereign](https://github.com/AHMADALIPARR/ace-sovereign) — the verified 6502 machine this runtime descends from

---

*Built to the poster. Verified by execution. Visuals start at the queue.*
