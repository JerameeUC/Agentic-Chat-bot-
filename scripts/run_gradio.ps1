param(
  [string]$Port = "7860",
  [string]$Host = "127.0.0.1"
)
$env:APP_MODE = "gradio"
$env:PORT = $Port
$env:HOST = $Host
python app\app.py