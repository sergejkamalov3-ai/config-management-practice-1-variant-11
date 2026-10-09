@echo off
cd /d "%~dp0.."
echo exit|python -m src.main
if errorlevel 1 exit /b 1
echo exit|python -m src.main --vfs examples/vfs/files.json
if errorlevel 1 exit /b 1
call :expect_ok python -m src.main --vfs examples/vfs/files.json --script examples/scripts/stage2.txt
if errorlevel 1 exit /b 1
call :expect_error python -m src.main --script examples/scripts/stage2_error.txt
if errorlevel 1 exit /b 1
call :expect_error python -m src.main --script examples/scripts/missing.txt
if errorlevel 1 exit /b 1
exit /b 0

:expect_ok
%*
if errorlevel 1 exit /b 1
exit /b 0

:expect_error
%*
if not errorlevel 1 exit /b 1
exit /b 0
