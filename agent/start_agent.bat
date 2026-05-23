@echo off
cd /d "%~dp0.."
call venv\Scripts\activate.bat
python agent\agent_server.py
