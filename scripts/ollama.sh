#!/bin/bash 

echo "\033[91m ollama init script started\033[m"

ollama serve & 
OLLAMA_PID=$!

echo "Waiting for Ollama server..." 
until ollama list >/dev/null 2>&1; do
    sleep 1 
done

# check if the model is already installed
if ollama list | grep -q "$LLM_MODEL"; then
    echo "Model $LLM_MODEL already exists"
else
    echo "Installing $LLM_MODEL..."
    ollama pull "$LLM_MODEL"
fi

#embeddings model
if ollama list | grep -q "$EMBEDDING_MODEL"; then
    echo "Embeddings model $EMBEDDING_MODEL already exists"
else
    echo "Installing embeddings model $EMBEDDING_MODEL..."
    ollama pull "$EMBEDDING_MODEL"
fi

wait # this is to keep the cotnaier running 