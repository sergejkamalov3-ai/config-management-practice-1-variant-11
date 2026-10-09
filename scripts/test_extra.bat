@echo off
cd /d "%~dp0.."
call :expect_ok python -m src.main --script examples/scripts/stage5.txt
if errorlevel 1 exit /b 1
for %%F in (examples\scripts\errors\*.txt) do (
    call :expect_error python -m src.main --script "%%F"
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
