@echo off
cd /d "%~dp0.."
for %%N in (minimal files deep) do (
    python -m src.main --vfs examples/vfs/%%N.json --script examples/scripts/stage3.txt
)
python -m src.main --vfs examples/vfs/missing.json
python -m src.main --vfs examples/vfs/invalid.json
