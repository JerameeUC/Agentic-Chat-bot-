@echo off
set APP_MODE=aiohttp
set PORT=%1
if "%PORT%"=="" set PORT=3978
set HOST=%2
if "%HOST%"=="" set HOST=127.0.0.1
python app\app.py