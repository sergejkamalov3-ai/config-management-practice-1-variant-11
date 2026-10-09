@echo off
cd /d "%~dp0.."
python -m src.main --script examples/scripts/stage4.txt
for %%F in (examples/scripts/errors/*.txt) do (
    python -m src.main --script examples/scripts/errors/%%~nxF
)
