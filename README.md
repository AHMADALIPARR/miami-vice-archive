# Miami Vice Archive — Execution Architecture

An execution architecture for archived source: BASIC listings from
Miami Vice Magazine enter as data, are parsed and lowered through a
6502 intermediate representation into ROPE/AGC assembly, and execute
in a container and memory runtime — banked memory, a declared memory
map, an I/O and GPU command queue — with Fortran compute and Vulkan
rendering layers behind the runtime and a Jetson as the native host.

The architecture is specified by the poster in
`docs/architecture-poster.jpg`. `BLUEPRINT.md` decomposes it into
components and records what already exists (the 6502 and AGC assembly
corpora in `6502-transformer`; the verified 6502 container machine in
`ace-sovereign`), what is partial, and what this build adds, stage by
stage. `STATUS.md` keeps the verified state separate from the staged
work.
