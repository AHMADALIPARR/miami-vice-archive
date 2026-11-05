# AGENTS.md — law of this repository

1. **Verify before commit.** Every stage lands with a test suite that
   runs its claims. A change that weakens a gate to make a test pass
   is a regression, not a fix.
2. **The owner's corpora are verbatim.** The 6502 and AGC assembly in
   6502-transformer is his code, kernels included; it is imported or
   referenced, never silently rewritten. Fixes are offered, not
   installed.
3. **Provenance is part of the build.** Code that descends from
   ace-sovereign says so where it lands. Archive inputs carry a
   provenance record and pass the checksum gate before anything
   executes them.
4. **Claims match execution.** STATUS.md separates verified facts from
   staged work. Do not promote a staged item without running it.
5. **License.** The sovereign license in LICENSE governs this layer.
   Check it before any push.
