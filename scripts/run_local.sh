# /scripts/run_local.sh
#!/usr/bin/env bash
set -Eeuo pipefail

# Move to repo root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# --- Configuration via env (with sane defaults) ---
export PYTHONPATH="${PYTHONPATH:-.}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7860}"
MODE="${MODE:-gradio}"   # gradio | uvicorn
RELOAD="${RELOAD:-false}" # only applies to MODE=uvicorn
INSTALL="${INSTALL:-0}"   # set INSTALL=1 to pip install requirements

# Load .env if present (ignore comments/blank lines)
if [[ -f .env ]]; then
  # shellcheck disable=SC2046
  export $(grep -vE '^\s*#' .env | grep -vE '^\s*$' | xargs -0 -I{} bash -c 'printf "%s\0" "{}"' 2>/dev/null || true)
fi

if [[ "$INSTALL" == "1" ]]; then
  echo "📦 Installing dependencies from requirements.txt ..."
  python -m pip install -r requirements.txt
fi

trap 'echo; echo "⛔ Server terminated";' INT TERM

if [[ "$MODE" == "uvicorn" ]]; then
  # Dev-friendly server with optional reload (expects FastAPI app factory)
  echo "▶ Starting Uvicorn on http://${HOST}:${PORT}  (reload=${RELOAD})"
  # If you expose a FastAPI app object directly, adjust target accordingly (e.g., storefront_chatbot.app.app:app)
  cmd=(python -m uvicorn storefront_chatbot.app.app:build --host "$HOST" --port "$PORT")
  [[ "$RELOAD" == "true" ]] && cmd+=(--reload)
  exec "${cmd[@]}"
else
  # Gradio path (matches your original build().launch)
  echo "▶ Starting Gradio on http://${HOST}:${PORT}"
  python - <<PY
from storefront_chatbot.app.app import build
app = build()
app.launch(server_name="${HOST}", server_port=${PORT})
PY
fi
