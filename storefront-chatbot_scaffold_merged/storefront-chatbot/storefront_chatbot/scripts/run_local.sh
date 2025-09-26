#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=.
python -c "from storefront_chatbot.app.app import build; build().launch(server_name='0.0.0.0', server_port=7860)"
