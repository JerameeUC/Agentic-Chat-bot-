param(
  [string]$Port = "8000",
  [string]$Host = "127.0.0.1"
)
uvicorn agenticcore.web_agentic:app --reload --host $Host --port $Port