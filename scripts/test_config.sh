#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
printf 'exit\n' | python3 -m src.main
python3 -m src.main --vfs examples/vfs/files.json --script examples/scripts/stage2.txt
if python3 -m src.main --script examples/scripts/stage2_error.txt; then
    exit 1
fi
if python3 -m src.main --script examples/scripts/missing.txt; then
    exit 1
fi
