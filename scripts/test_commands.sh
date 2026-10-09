#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m src.main --script examples/scripts/stage4.txt
for file in examples/scripts/errors/*.txt; do
    if python3 -m src.main --script "$file"; then
        exit 1
    fi
done
