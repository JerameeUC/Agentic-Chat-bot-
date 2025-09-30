param(
  [string]$Port = "3978",
  [string]$Host = "127.0.0.1"
)
$env:APP_MODE = "aiohttp"
$env:PORT = $Port
$env:HOST = $Host
python app\app.py