#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
for name in minimal files deep; do
    python3 -m src.main --vfs "examples/vfs/$name.json" \
        --script examples/scripts/stage3.txt
done
for name in missing invalid; do
    if python3 -m src.main --vfs "examples/vfs/$name.json"; then
        exit 1
    fi
done
