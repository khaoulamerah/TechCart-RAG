
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/root/.cache/huggingface \
    HF_HUB_DISABLE_XET=1

WORKDIR /app

# Install the CPU-only PyTorch build.
# Longer timeouts and retries help with slow network connections.
RUN python -m pip install \
        --no-cache-dir \
        --timeout 300 \
        --retries 10 \
        --index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        "torch==2.7.1+cpu"

# Keep the reranker dependencies separate from backend requirements.
COPY services/reranker/requirements.txt /tmp/requirements.txt

RUN python -m pip install \
        --no-cache-dir \
        --timeout 300 \
        --retries 10 \
        --index-url https://pypi.org/simple \
        -r /tmp/requirements.txt

# Copy the reranker service source code.
COPY services/reranker/ /app/

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
