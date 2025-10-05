# scripts/seed_storefront.py
"""Seed the RAG store with the storefront knowledge pack.
Usage:
  python -m scripts.seed_storefront --source memory/rag/data/storefront
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='memory/rag/data/storefront', help='Folder with storefront docs')
    p.add_argument('--rebuild', action='store_true', help='Rebuild index from scratch')
    args = p.parse_args()

    try:
        from memory.rag.indexer import build_index_for_path
    except Exception as e:
        print('[seed_storefront] Could not import memory.rag.indexer — ensure repo root.', file=sys.stderr)
        print('Error:', e, file=sys.stderr)
        sys.exit(2)

    src = Path(args.source).resolve()
    if not src.exists():
        print(f'[seed_storefront] Source not found: {src}', file=sys.stderr)
        sys.exit(2)

    print(f'[seed_storefront] Indexing: {src}')
    build_index_for_path(str(src), rebuild=args.rebuild)

if __name__ == '__main__':
    main()
