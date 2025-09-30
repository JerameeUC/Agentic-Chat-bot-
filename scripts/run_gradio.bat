@echo off
set APP_MODE=gradio
set PORT=%1
if "%PORT%"=="" set PORT=7860
set HOST=%2
if "%HOST%"=="" set HOST=127.0.0.1
python app\app.py