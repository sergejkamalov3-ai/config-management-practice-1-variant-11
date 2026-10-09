@echo off
cd /d "%~dp0.."
echo exit|python -m src.main
python -m src.main --vfs examples/vfs/files.json --script examples/scripts/stage2.txt
python -m src.main --script examples/scripts/stage2_error.txt
python -m src.main --script examples/scripts/missing.txt
