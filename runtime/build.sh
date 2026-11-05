#!/usr/bin/env bash
# build.sh — compile the 6502 machine and its assembler. OTP only.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/ebin"
erlc -o "$HERE/ebin" "$HERE/src/mv6502.erl" "$HERE/src/mv_asm.erl"
echo "built: $HERE/ebin"
