# /agenticcore/cli.py
"""
agenticcore.cli
Console entrypoints:
  - agentic: send a message to ChatBot and print reply JSON
  - repo-tree: print a filtered tree view (uses tree.txt if present)
  - repo-flatten: flatten code listing to stdout (uses FLATTENED_CODE.txt if present)
"""
import argparse, json, sys, traceback
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env variables into os.environ (project root .env by default)
load_dotenv()


def cmd_agentic(argv=None):
    # Lazy import so other commands don't require ChatBot to be importable
    from agenticcore.chatbot.services import ChatBot
    # We call analyze_sentiment only for 'status' to reveal the actual chosen provider
    try:
        from agenticcore.providers_unified import analyze_sentiment
    except Exception:
        analyze_sentiment = None  # still fine; we'll show mode only

    p = argparse.ArgumentParser(prog="agentic", description="Chat with AgenticCore ChatBot")
    p.add_argument("message", nargs="*", help="Message to send")
    p.add_argument("--debug", action="store_true", help="Print debug info")
    args = p.parse_args(argv)
    msg = " ".join(args.message).strip() or "hello"

    if args.debug:
        print(f"DEBUG argv={sys.argv}", flush=True)
        print(f"DEBUG raw message='{msg}'", flush=True)

    bot = ChatBot()

    # Special commands for testing / assignments
        # Special commands for testing / assignments
    if msg.lower() == "status":
        import requests  # local import to avoid hard dep for other commands

        # Try a lightweight provider probe via analyze_sentiment
        provider = None
        if analyze_sentiment is not None:
            try:
                probe = analyze_sentiment("status ping")
                provider = (probe or {}).get("provider")
            except Exception:
                if args.debug:
                    traceback.print_exc()

        # Hugging Face whoami auth probe
        tok = os.getenv("HF_API_KEY", "")
        who = None
        auth_ok = False
        err = None
        try:
            if tok:
                r = requests.get(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {tok}"},
                    timeout=15,
                )
                auth_ok = (r.status_code == 200)
                who = r.json() if auth_ok else None
                if not auth_ok:
                    err = r.text  # e.g., {"error":"Invalid credentials in Authorization header"}
            else:
                err = "HF_API_KEY not set (load .env or export it)"
        except Exception as e:
            err = str(e)

        # Extract fine-grained scopes for visibility
        fg = (((who or {}).get("auth") or {}).get("accessToken") or {}).get("fineGrained") or {}
        scoped = fg.get("scoped") or []
        global_scopes = fg.get("global") or []

        # ---- tiny inference ping (proves 'Make calls to Inference Providers') ----
        infer_ok, infer_err = False, None
        try:
            if tok:
                model = os.getenv(
                    "HF_MODEL_SENTIMENT",
                    "distilbert-base-uncased-finetuned-sst-2-english"
                )
                r2 = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {tok}", "x-wait-for-model": "true"},
                    json={"inputs": "ping"},
                    timeout=int(os.getenv("HTTP_TIMEOUT", "60")),
                )
                infer_ok = (r2.status_code == 200)
                if not infer_ok:
                    infer_err = f"HTTP {r2.status_code}: {r2.text}"
        except Exception as e:
            infer_err = str(e)
        # -------------------------------------------------------------------------

        # Mask + length to verify what .env provided
        mask = (tok[:3] + "..." + tok[-4:]) if tok else None
        out = {
            "provider": provider or "unknown",
            "mode": getattr(bot, "_mode", "auto"),
            "auth_ok": auth_ok,
            "whoami": who,
            "token_scopes": {            # <--- added
                "global": global_scopes,
                "scoped": scoped,
            },
            "inference_ok": infer_ok,
            "inference_error": infer_err,
            "env": {
                "HF_API_KEY_len": len(tok) if tok else 0,
                "HF_API_KEY_mask": mask,
                "HF_MODEL_SENTIMENT": os.getenv("HF_MODEL_SENTIMENT"),
                "HTTP_TIMEOUT": os.getenv("HTTP_TIMEOUT"),
            },
            "capabilities": bot.capabilities(),
            "error": err,
        }

    elif msg.lower() == "help":
        out = {"capabilities": bot.capabilities()}

    else:
        try:
            out = bot.reply(msg)
        except Exception as e:
            if args.debug:
                traceback.print_exc()
            out = {"error": str(e), "message": msg}

    if args.debug:
        print(f"DEBUG out={out}", flush=True)

    print(json.dumps(out, indent=2), flush=True)


def cmd_repo_tree(argv=None):
    p = argparse.ArgumentParser(prog="repo-tree", description="Print repo tree (from tree.txt if available)")
    p.add_argument("--path", default="tree.txt", help="Path to precomputed tree file")
    args = p.parse_args(argv)
    path = Path(args.path)
    if path.exists():
        print(path.read_text(encoding="utf-8"), flush=True)
    else:
        print("(no tree.txt found)", flush=True)


def cmd_repo_flatten(argv=None):
    p = argparse.ArgumentParser(prog="repo-flatten", description="Print flattened code listing")
    p.add_argument("--path", default="FLATTENED_CODE.txt", help="Path to pre-flattened code file")
    args = p.parse_args(argv)
    path = Path(args.path)
    if path.exists():
        print(path.read_text(encoding="utf-8"), flush=True)
    else:
        print("(no FLATTENED_CODE.txt found)", flush=True)


def _dispatch():
    # Allow: python -m agenticcore.cli <subcommand> [args...]
    if len(sys.argv) <= 1:
        print("Usage: python -m agenticcore.cli <agentic|repo-tree|repo-flatten> [args]", file=sys.stderr)
        sys.exit(2)
    cmd, argv = sys.argv[1], sys.argv[2:]
    try:
        if cmd == "agentic":
            cmd_agentic(argv)
        elif cmd == "repo-tree":
            cmd_repo_tree(argv)
        elif cmd == "repo-flatten":
            cmd_repo_flatten(argv)
        else:
            print(f"Unknown subcommand: {cmd}", file=sys.stderr)
            sys.exit(2)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    _dispatch()
