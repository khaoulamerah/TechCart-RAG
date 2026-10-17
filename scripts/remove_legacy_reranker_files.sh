#!/usr/bin/env sh
set -eu
# Run from the project root after applying the HTTP reranker patch.
rm -f backend/rag/reranker/qwen3_transformers.py
rm -f tests/test_qwen3_transformers_reranker.py
rm -f tests/test_ollama_reranker.py
printf '%s\n' "Removed legacy local/Ollama reranker files."
