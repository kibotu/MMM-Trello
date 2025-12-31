@echo off
echo Starting MMM-Trello Test Server with uv...
cd /d "%~dp0"
uv run test-server.py
pause
