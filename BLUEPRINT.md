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

### Compute layer (Pascal controls, Vulkan executes — CUDA-free)
The owner's layering (2026-11-04), which replaces the poster's
CUDA/Fortran box:

- **Pascal: the compute language and kernel definitions.** Numerical
  algorithms, tensor operations, transformations, and simulation
  logic are written in Pascal. The system is CUDA-free at the
  application level: Pascal controls compute, Vulkan executes it —
  not CUDA calls wrapped in Pascal.
- **The critical component: a Pascal-to-SPIR-V compiler / lowering
  path.** Without it, ordinary Free Pascal code runs on the ARM64 CPU
  rather than the GPU. The lowering covers a restricted kernel
  subset — fixed bounds, pure arithmetic, no heap, no strings, no
  I/O — which is the shape the owner's kernels already have. First
  corpus: his Pascal arithmetic kernels for the ternary model.
  Routes: a direct SPIR-V emitter from the subset's IR, with a
  GLSL + glslang bridge as a bootstrap; both end at the same
  artifact, a validated SPIR-V module.
- **Vulkan: GPU compute, rendering, and synchronization.** Compute
  shaders compiled to SPIR-V execute the GPU workloads; the render
  layer below is the same API's other half.
- **Fortran: optional numerical routines** (CPU-side). The owner's
  Fortran kernels exist in his other repos (e.g. preeny-sovereign's
  `sovereign_math` / `sovereign_vector`).
- **ROPE/AGC: deterministic execution and instruction control.**
  Kernel launches are commands in the runtime's stream (through the
  $C000 queue), issued by the deterministic layer — not host-side
  imperative calls.
- **Jetson unified memory:** shared physical memory with explicit
  buffer ownership and synchronization; ownership is recorded, the
  same discipline as the ledger.

### What the Vulkan end needs (Stage 6 bill of materials)

Everything except the seam is off the shelf; nothing on this list
needs a vendor account or token.

1. **The driver** — already on the Jetson: JetPack/L4T ships the
   NVIDIA Vulkan ICD and loader. No CUDA toolkit anywhere in the
   chain.
2. **The host binding** — a small native host process owns the
   Vulkan device and takes orders from the runtime (the ACE pattern:
   the harness dispatches, the native end executes). The open-source
   candidates the owner pointed at: **Vulkan-Hpp** (KhronosGroup,
   header-only C++ bindings) or **Silk.NET** (.NET Foundation, C#
   bindings). C++/Vulkan-Hpp keeps the host dependency-free; C#
   pulls a .NET runtime onto the Jetson. Owner's call.
3. **The SPIR-V gate** — glslang (the bootstrap compiler) and
   SPIRV-Tools' `spirv-val`: every module the Pascal lowering emits
   is validated before the host loads it. Verified artifacts only.
4. **The seam (ours to design)** — the command vocabulary over the
   runtime's GPU queue. The CPU side already exists (Stage 1: writes
   to $C100–$CFFF drain as ordered {address, byte} commands). The
   host side needs the opcode table those bytes map to: buffer
   create/copy, pipeline bind, dispatch, present — a display list,
   decided by ROPE/AGC, executed by Vulkan.
5. **Buffers on unified memory** — host-visible, host-coherent
   allocations so the Pascal/BEAM side and the GPU share physical
   memory with no copies; each buffer carries an ownership record
   (which layer owns it, when ownership transfers) and
   synchronization is explicit (fences / timeline semaphores),
   never assumed.

### Stage 6 build-out — everything needed

**Repository (owner's order, 2026-11-04):** Stage 6 is its own
repo, `jetson-vulkan-host` (local), with the upstream source
*extracted into it* — seven Khronos trees vendored under `vendor/`
with pinned commits in its SOURCES.md (223 MB: Vulkan-Headers,
Vulkan-Loader, Vulkan-Hpp, SPIRV-Headers, SPIRV-Tools, glslang,
Vulkan-ValidationLayers). Its BUILD-PLAN.md carries the write list.

**Fetch (all open source, no accounts, no tokens):**
- Vulkan-Headers + Vulkan-Loader (KhronosGroup) — or the loader
  JetPack already ships; headers are the part to pin.
- Vulkan-Hpp (KhronosGroup) for the C++ host, per the bill above.
- glslang + SPIRV-Headers + SPIRV-Tools (KhronosGroup) — the
  bootstrap compiler and the validator.
- Vulkan-ValidationLayers (KhronosGroup) — development-time checks
  on the host's own API usage.
- Free Pascal for ARM64 — the Pascal kernels' compiler and the
  lowering's front end.
- A C++ compiler on the Jetson (gcc from JetPack suffices).

**Write (the actual build, in dependency order):**
1. *Device probe* — a throwaway program that opens the Orin GPU
   through the loader and prints its properties and queue families.
   Proves the driver path before anything is built on it.
2. *The host daemon* (C++/Vulkan-Hpp) — instance, device, compute
   queue, command pool, descriptor layout for storage buffers; a
   control channel the BEAM harness drives (Unix socket, line
   protocol — the ace-sovereign harness pattern).
3. *The buffer manager* — host-visible/coherent pools plus the
   ownership table: every buffer has an owning layer, a state, and
   a transfer log; the GPU touches a buffer only under a recorded
   transfer.
4. *The SPIR-V gate + module registry* — spirv-val in the load
   path; modules admitted by hash, once, into a registry mapping
   hash → pipeline.
5. *First workload* — the owner's ternary kernel as a compute
   shader, dispatched over a buffer. Gate: GPU results equal the
   Pascal CPU reference exactly (integer kernels — no tolerances).
6. *The queue seam* — the opcode table for the runtime's GPU queue
   (Stage 1 drains {address, byte} pairs): buffer create/copy,
   pipeline bind, dispatch, present; a BEAM-side translator turns
   the drained stream into host-daemon commands, deterministically.
7. *Render half* — offscreen target with readback/capture first;
   swapchain/display last, if at all.
8. *Sync hardening* — fences/timeline semaphores wired to the
   ownership table; no implicit waits.

**Not needed:** CUDA toolkit, cuDNN, Nsight, vendor SDK accounts,
cloud services of any kind.

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

## Division of labor (owner, 2026-11-04)

- **The owner's end: Stage 6** — the Pascal-to-SPIR-V path and the
  Vulkan execution layer on the Jetson (C# and C++ on the Vulkan side,
  from an open-source repo he will name).
- **Muse's carve: Stages 1–5** — runtime, verification + intake,
  ROPE/AGC core, front end, lowering, built and verified here.

## Stage plan

1. **Memory & container runtime to the poster's map** — BUILT
   2026-11-04: `runtime/` holds `mv6502` (CPU core descended from
   ace6502; banked window over $0200–$7FFF with the bank register at
   $C000, dedicated zero page and stack, runtime RAM $8000–$BFFF,
   GPU command queue window $C100–$CFFF, vector shadow at the top of
   I/O space) and `mv_asm`. Verified: suite 4/4 with 16 checks — the
   11 ace6502 CPU regression vectors unchanged, plus bank isolation,
   bank-register wrap and readback, queue capture, zero-page and
   runtime-region behaviour.
2. **Verification service + archive intake** — checksum/CRC gate;
   a listing enters only with a provenance record and a passing sum.
3. **ROPE/AGC core** — assembler for the corpus's AGC subset, linker
   (containers/banks), loader onto the Stage-1 map; the corpus's
   kernels assemble and run.
4. **Front end** — PureBasic parser for the magazine-listing subset →
   6502 IR → Stage-1 runtime: the first listing executes end to end.
5. **Lowering** — 6502 IR → ROPE/AGC, proven on the corpus's kernels.
6. **Compute + render + Jetson** — the Pascal-to-SPIR-V lowering
   (subset compiler; the ternary kernels as its first corpus),
   optional Fortran routines, Vulkan compute + render executing the
   SPIR-V, unified-memory buffer ownership, deployment. Toolchain
   note: no fpc / glslang / SPIR-V tools / Vulkan on this VM yet —
   Jetson-stage provisioning.

Every stage ends at the same bar as the rest of the owner's work:
verified by execution, staged claims in STATUS.md, nothing published
without his go-ahead and a named destination.
