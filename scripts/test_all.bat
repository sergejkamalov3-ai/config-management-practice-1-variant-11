@echo off
cd /d "%~dp0.."
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
call scripts\test_config.bat
if errorlevel 1 exit /b 1
call scripts\test_vfs.bat
if errorlevel 1 exit /b 1
call scripts\test_commands.bat
if errorlevel 1 exit /b 1
call scripts\test_extra.bat
if errorlevel 1 exit /b 1
exit /b 0
