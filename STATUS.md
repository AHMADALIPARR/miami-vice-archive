# STATUS

## State at blueprint (2026-11-04)

- The specification poster is filed at `docs/architecture-poster.jpg`.
- The component map in BLUEPRINT.md was audited against the workspace:
  - `AHMADALIPARR/6502-transformer` (local, master `b6acddc`) holds the
    6502 and AGC assembly corpora on the owner's verbatim kernels —
    written, never executed.
  - `AHMADALIPARR/ace-sovereign` (published 2026-11-04, master
    `934d617`) holds the verified 6502 container machine, assembler,
    sandbox lifecycle, harness, and tunnel this build's runtime
    descends from.
  - `legacy-logic-archive` was checked and is a different archive
    (historical logic-programming corpus) — not an input to this build.
  - No Miami Vice Magazine BASIC listing has been located in the
    workspace yet; the first listing is the owner's to supply.
- Division of labor (owner, 2026-11-04): Stage 6 (Pascal-to-SPIR-V +
  Vulkan on the Jetson) is the owner's end; Stages 1–5 are carved out
  here.

## Stage 1 — memory & container runtime (2026-11-04)

- `runtime/src/mv6502.erl`: the banked runtime CPU. The instruction
  engine descends unchanged from ace-sovereign's ace6502 (provenance
  in the module header); the memory layer implements the poster's
  map: dedicated zero page + stack, banked program/data window
  $0200–$7FFF (bank register at $C000, wraps by rem, reads back),
  runtime RAM $8000–$BFFF, GPU command queue window $C100–$CFFF
  (writes captured as {address, byte}, nothing stored), $FE00/$FE01
  ports, vector shadow $FFFA–$FFFF.
- `runtime/src/mv_asm.erl`: the assembler, descended the same way.
- Verified by execution: `runtime/test/run-runtime-test.sh` — 4/4,
  with all 16 checks inside passing: the 11 ace6502 CPU regression
  vectors (arithmetic, loops, JSR, BCD, the JMP-indirect quirk, the
  650 sum-of-squares cross-check, and the rest) plus bank isolation
  (one address, three banks, outputs 0 / $AA / $BB in order), bank
  register wrap (7 rem 4 = 3) and readback, queue capture order,
  zero page surviving bank switches, runtime-region round trip.
- Next: Stage 2 (verification service + archive intake).

## Software visual host (2026-11-07)

- `visual/queue_renderer.py`: consumes the Stage-1 GPU queue format
  (ordered {address, byte} writes) and produces a 320×240 PNG.
  Opcode vocabulary: SET_COLOR, FILL_RECT, DRAW_LINE, CLEAR, TEXT,
  PRESENT. Absolute addresses ignored; only write order matters.
- `visual/sample_queue.py`: emits a branded command stream that
  renders a near-black / brass / paper frame with the wordmark.
- This is the software stand-in for the queue seam. The real Vulkan
  host (Stage 6) remains the owner's carve in a separate repo.

## Repository state

Working name `miami-vice-archive`. License: the sovereign license in
`LICENSE`, copied verbatim.
