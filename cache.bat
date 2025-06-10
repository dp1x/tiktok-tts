@echo off
echo Closing Windows Explorer...
taskkill /f /im explorer.exe

echo Deleting Icon Cache files...
del /a /q "%localappdata%\IconCache.db"
del /a /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*"

echo Starting Windows Explorer...
start explorer.exe

echo.
echo Icon Cache has been cleared. Please restart your computer for all changes to take full effect.
pause