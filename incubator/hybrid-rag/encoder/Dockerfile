FROM ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d AS uv
FROM python:3.11.14-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev
COPY rag_models ./rag_models
ENTRYPOINT ["python", "-m", "uvicorn", "rag_models.api:from_environment", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
