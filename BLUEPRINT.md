# Blueprint — Miami Vice Magazine Archive Execution Architecture

The specification is the poster (`docs/architecture-poster.jpg`): archive
source listings enter at the left, are lowered through a 6502 IR into
ROPE/AGC assembly, execute in a container and memory runtime, and reach
Fortran/Pascal compute and Vulkan rendering on the Jetson. This document
decomposes the poster into components and records, for each one, what
already exists, what is partial, and what is missing. "Half of it
already exists" is the owner's assessment; the map below is the audit
of that claim against the repos on disk.

## Pipeline (the poster's top strip)

PureBasic (source from Miami Vice Magazine) → 6502 Semantic Lowering
(compatible 6502 IR) → ROPE / AGC Assembly (custom ISA) → Container &
Memory Runtime (emulated 6502 + ROPE/AGC) → Pascal / Fortran Compute
(numerics, DSP, AI, media) → Vulkan Rendering (graphics, video, UI).

## Component map

### Source inputs (from archive)
- **BASIC listings (Miami Vice Magazine)** — not yet located in the
  workspace. The intake format (Stage 2) takes a listing plus a
  provenance record; the first listing is the owner's to supply.
- **Machine code / assembly (reconstructions)** — EXISTS:
  `AHMADALIPARR/6502-transformer` holds the 6502 corpus (`ternary_dot`,
  `forward`, `backward`, `math`, `memmap`, `main`) and the AGC corpus
  (`ternary_squib`, `forward`, `backward`, `math`, `main.agc`, ~5,300
  lines total), built on the owner's verbatim kernels. Written, never
  executed — no assembler or emulator was available when it landed.
- **Memory routines (alloc / banks / I/O)** — PARTIAL: `6502/memmap.asm`
  and the `math` units exist as sources; bank behaviour is specified by
  the poster's map (below), not yet by running code.
- **Checksum algorithms (verification)** — MISSING as a service;
  Stage 2 builds the checksum/CRC gate every archive input passes.

### Front end
- **PureBasic Parser** — MISSING. The toolchain is present and proven
  on this machine (PureBasic 6.41 demo, C backend; the owner's
  Voxel800.pb compiles and runs headlessly).
- **6502 IR (instruction & control flow)** — PARTIAL: the term form in
  ace-sovereign's `ace_asm` (labelled instruction terms the assembler
  and machine share) is the IR seed.
- **Lowering (6502 → ROPE/AGC)** — MISSING. The AGC corpus is a
  hand-written parallel implementation, not a lowering; Stage 5 builds
  the lowering the poster draws.

### ROPE / AGC core
- **Assembler** — PARTIAL: `ace_asm` assembles 6502 from the machine's
  own opcode table. An AGC assembler for the corpus's instruction
  subset does not exist here (the sources target yaAGC, unavailable).
- **Linker (containers / banks)** — MISSING (Stage 3).
- **Loader (memory mapping)** — PARTIAL: ace6502 loads a binary at an
  origin and full 64 KB images with a reset vector.

### Memory & container runtime
- **Memory map (poster)** — $0000–$00FF zero page / runtime;
  $0100–$01FF stack; $0200–$7FFF program / data banks; $8000–$BFFF
  ROPE/AGC runtime; $C000–$FFFF I/O / GPU command queue.
- **State** — PARTIAL: ace-sovereign's ace6502 is a flat 64 KB machine
  with a $FE00 output port and a step budget, verified by execution.
  Bank switching over the program/data window and the $C000 command
  queue are Stage 1 of this build. The container format is
  ace-sovereign's sbx (copy-on-write sandboxes, hash-chained ledger).
- **I/O abstraction (video / input / disk)** — PARTIAL: the output
  port exists; input and disk channels are Stage 1 alongside the queue.

### Compute layer (Pascal / Fortran)
- **Fortran modules (legacy algorithms)** — the owner's Fortran
  kernels exist in his other repos (e.g. preeny-sovereign's
  `sovereign_math` / `sovereign_vector`); this build's Fortran stage
  is verifiable on this machine.
- **Pascal kernels** — RESOLVED (owner, 2026-11-04): the poster names
  CUDA; the owner replaced it with Pascal — "that's actually better" —
  matching his standing rule that his kernels run Pascal instead of
  CUDA. The compute layer is Fortran + Pascal; the GPU half is
  Jetson-stage.

### Render layer (Vulkan)
- **GPU command translation (ROPE/AGC → Vulkan)** — MISSING; the
  $C000 command queue is its input contract, designable and testable
  at the queue level on this machine.
- **Rendering pipeline / frame output** — Jetson-gated.

### System services
- File / asset I/O (the sbx trees), input, timing & sync (the step
  budget is the deterministic sync seed), diagnostics (the hash-chained
  ledger), verification (Stage 2's checksum gate).

### Jetson native execution
ARM64 host runtime (BEAM runs there), unified memory, containerized
deployment (sbx + the machine). Nothing in Stages 1–5 depends on the
Jetson; Stage 6 lands there.

## Stage plan

1. **Memory & container runtime to the poster's map** — banked 6502
   runtime in this repo (CPU core lineage from ace6502, provenance
   recorded), $C000 I/O + GPU command queue, container format.
   Verified by machine tests.
2. **Verification service + archive intake** — checksum/CRC gate;
   a listing enters only with a provenance record and a passing sum.
3. **ROPE/AGC core** — assembler for the corpus's AGC subset, linker
   (containers/banks), loader onto the Stage-1 map; the corpus's
   kernels assemble and run.
4. **Front end** — PureBasic parser for the magazine-listing subset →
   6502 IR → Stage-1 runtime: the first listing executes end to end.
5. **Lowering** — 6502 IR → ROPE/AGC, proven on the corpus's kernels.
6. **Compute + render + Jetson** — Fortran modules and Pascal kernels
   wired to the runtime; command-queue → Vulkan translation;
   deployment.

Every stage ends at the same bar as the rest of the owner's work:
verified by execution, staged claims in STATUS.md, nothing published
without his go-ahead and a named destination.
