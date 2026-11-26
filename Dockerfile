# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.22 AS uv
FROM python:3.13.16-slim-bookworm AS dependencies

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.13.16-slim-bookworm
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
COPY --from=dependencies /opt/venv /opt/venv
COPY app.py ./
COPY .streamlit/config.toml .streamlit/config.toml
COPY assets ./assets
COPY mannsahara ./mannsahara
COPY prompts ./prompts
COPY evidence ./evidence

USER app
EXPOSE 8501
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).close()"]
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
