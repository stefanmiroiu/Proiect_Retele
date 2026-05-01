@echo off
cd /d "%~dp0"
start "Server UDP" cmd /k "title Server & py -m server.py"
timeout /t 1 /nobreak >nul
start "Client 1" cmd /k "title Client 1 & py -m client.py"
start "Client 2" cmd /k "title Client 2 & py -m client.py"
start "Client 3" cmd /k "title Client 3 & py -m client.py"
