@echo off
set PORT=%1
if "%PORT%"=="" set PORT=8000
set HOST=%2
if "%HOST%"=="" set HOST=127.0.0.1
uvicorn agenticcore.web_agentic:app --reload --host %HOST% --port %PORT%