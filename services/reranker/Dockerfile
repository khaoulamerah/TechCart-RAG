FROM python:3.11-slim

LABEL maintainer="TechCart"
LABEL description="TechCart Qwen3 reranker HTTP service"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    HF_HOME=/root/.cache/huggingface \
    HF_HUB_DISABLE_XET=1 \
    HF_HUB_ETAG_TIMEOUT=10 \
    HF_HUB_DOWNLOAD_TIMEOUT=60 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    TOKENIZERS_PARALLELISM=false

WORKDIR /app

RUN python -m pip install \
        --no-cache-dir \
        --timeout 300 \
        --retries 10 \
        --index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        "torch==2.7.1+cpu"

COPY services/reranker/requirements.txt /tmp/requirements.txt
RUN python -m pip install \
        --no-cache-dir \
        --timeout 300 \
        --retries 10 \
        --index-url https://pypi.org/simple \
        -r /tmp/requirements.txt

COPY services/reranker/ /app/

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
