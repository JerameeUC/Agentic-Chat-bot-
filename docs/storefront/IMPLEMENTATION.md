# Storefront Drop-In (Cap & Gown + Parking)

This pack is designed to be **dropped into the existing Agentic-Chat-bot repo** and indexed by its RAG layer.

## Where to drop files

- Copy `memory/rag/data/storefront/` into your repo's `memory/rag/data/`.
- Copy `docs/storefront/` alongside your current `docs/` folder.
- Optional: Copy `app/assets/html/storefront_frontend.html` to `app/assets/html/`.

## Indexing

Use the provided `scripts/seed_storefront.py` or your own pipeline to index:

```bash
python -m scripts.seed_storefront --source memory/rag/data/storefront
```

This calls `memory.rag.indexer` to build/update the vector store.

## Retrieval

Documents enable FAQs such as:
- Can I buy more than one parking pass? → **Yes**.
- Is formal attire required? → **Recommended, not required**.
- What parking rules apply? → **No double parking; handicap violators towed**.
