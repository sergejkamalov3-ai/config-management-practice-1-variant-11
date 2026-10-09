@echo off
cd /d "%~dp0.."
for %%N in (minimal files deep) do (
    call :expect_ok python -m src.main --vfs examples/vfs/%%N.json --script examples/scripts/stage3.txt
    if errorlevel 1 exit /b 1
)
for %%N in (missing invalid) do (
    call :expect_error python -m src.main --vfs examples/vfs/%%N.json
    if errorlevel 1 exit /b 1
)
exit /b 0

:expect_ok
%*
if errorlevel 1 exit /b 1
exit /b 0

:expect_error
%*
if not errorlevel 1 exit /b 1
exit /b 0
