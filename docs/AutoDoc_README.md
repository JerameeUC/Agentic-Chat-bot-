# 📘 Auto-Documentation Guide (pdoc)

This project uses **[pdoc](https://pdoc.dev/)** to automatically generate HTML documentation from the Python source code.  
It introspects docstrings, function signatures, and type hints for the following packages:

```
anon_bot
app
backend
guardrails
integrations
logged_in_bot
memory
nlu
scripts
test
```

---

## 🧰 Requirements

Install `pdoc` inside your project’s virtual environment:

```bash
pip install pdoc
```

---

## ⚙️ Environment Setup

Before building documentation, set these environment variables to make imports safe:

```powershell
$env:ENABLE_LLM = "0"
$env:PYTHONPATH = (Get-Location).Path
```

This disables runtime logic (e.g., Azure/OpenAI calls) during import and ensures pdoc can find local packages.

---

## 🧩 Generate Documentation

### ✅ Normal mode (strict)
Use this once your imports are clean:

```powershell
pdoc anon_bot app backend guardrails integrations logged_in_bot memory nlu scripts test -o docs/site
```

This will:
- Import each listed module.
- Generate static HTML documentation into `docs/site/`.
- Fail if any module raises an import error.

---

### ⚠️ Workaround mode (skip-errors)
While the project is still under development, use this safer variant:

```powershell
pdoc --skip-errors anon_bot app backend guardrails integrations logged_in_bot memory nlu scripts test -o docs/site
```

This tells pdoc to **skip modules that fail to import** and continue generating docs for the rest.  
Use this as the default workflow until all packages have proper relative imports and no external dependency errors.

---

## 🌐 Preview Documentation

After generation, open:

```
docs/site/index.html
```

Or start a local preview server:

```bash
pdoc --http :8080 anon_bot app backend guardrails integrations logged_in_bot memory nlu scripts test
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

---

## 🧹 Tips for Clean Imports

- Ensure every package has an `__init__.py`.
- Use **relative imports** within packages (e.g., `from .rules import route`).
- Wrap optional dependencies with `try/except ImportError`.
- Avoid API calls or side-effects at the top level.
- Export only necessary symbols via `__all__`.

---

## 📁 Output Structure

```
docs/
  ├── site/
  │   ├── index.html
  │   ├── anon_bot.html
  │   ├── backend.html
  │   └── ...
  └── (future readme assets, CSS overrides, etc.)
```

---

## ✅ Next Steps

- Remove `--skip-errors` once all import paths and shims are fixed.
- Optionally integrate pdoc into your CI/CD pipeline or GitHub Pages by serving from `/docs/site`.

---

*Last updated: October 2025*
