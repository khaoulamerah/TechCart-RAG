#!/usr/bin/env bash
set -Eeuo pipefail

printf '\033[36m%s\033[0m\n' "TechCart Ollama initialization started"

: "${LLM_MODEL:?LLM_MODEL must be configured}"
: "${EMBEDDING_MODEL:?EMBEDDING_MODEL must be configured}"

# Do not let a marker from a previous container run report stale readiness.
rm -f /tmp/techcart-models-ready

ollama serve &
OLLAMA_PID=$!

cleanup() {
    kill "${OLLAMA_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

printf '%s\n' "Waiting for Ollama API..."
until ollama list >/dev/null 2>&1; do
    if ! kill -0 "${OLLAMA_PID}" 2>/dev/null; then
        echo "Ollama server exited before becoming ready." >&2
        exit 1
    fi
    sleep 1
done

ensure_model() {
    local model="$1"
    local installed_models

    installed_models="$(ollama list | awk 'NR > 1 { print $1 }')"
    if grep -Fxq -- "${model}" <<<"${installed_models}"; then
        printf 'Model already installed: %s\n' "${model}"
    elif [[ "${model}" != *:* ]] && grep -Fxq -- "${model}:latest" <<<"${installed_models}"; then
        printf 'Model already installed: %s:latest\n' "${model}"
    else
        printf 'Pulling model: %s\n' "${model}"
        ollama pull "${model}"
    fi
}

# Ollama now serves only the chat LLM and the embedding model.
# Qwen3-Reranker is loaded separately by Transformers in the backend.
ensure_model "${LLM_MODEL}"
ensure_model "${EMBEDDING_MODEL}"

touch /tmp/techcart-models-ready
printf '%s\n' "Configured Ollama chat and embedding models are ready."

wait "${OLLAMA_PID}"
