# Miami Vice Archive

![Architecture Poster](docs/architecture-poster.jpg)

**A verified 6502 container runtime that executes archived source on the memory map drawn in the poster.**

This is not a finished game. It is the execution architecture that will eventually run BASIC listings from Miami Vice Magazine (and related machine-code reconstructions). Listings enter as data, are lowered through a 6502 IR into ROPE/AGC assembly, and run inside a banked memory runtime with a declared map, an I/O port, and a GPU command queue. Compute and rendering layers sit behind it; the native host is a Jetson.

The poster above is the specification. Everything below is what actually runs today.

## What runs today (Stage 1)

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

## What does not run yet

- No Miami Vice Magazine BASIC listing has been ingested.
- No PureBasic parser, no 6502-to-ROPE/AGC lowering, no AGC assembler for the corpus.
- No Vulkan host, no SPIR-V, no off-screen framebuffer, no present. Visual output is Stage 6 (`jetson-vulkan-host`).
- There are no gameplay screenshots because there is no game binary and no render path.

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
Pascal / Fortran compute
    ↓
Vulkan render (Stage 6)
```

## Documents

- [BLUEPRINT.md](BLUEPRINT.md) — component map, what exists, stage plan 1–6
- [STATUS.md](STATUS.md) — verified facts vs. staged work
- [AGENTS.md](AGENTS.md) — repository laws (verify before commit, provenance, claims match execution)
- [LICENSE](LICENSE) — sovereign license

## Related

- [6502-transformer](https://github.com/AHMADALIPARR/6502-transformer) — 6502 and AGC corpora
- [ace-sovereign](https://github.com/AHMADALIPARR/ace-sovereign) — the verified 6502 machine this runtime descends from

---

*Built to the poster. Verified by execution. Visuals come later.*
