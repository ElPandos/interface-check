FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build

WORKDIR /app

RUN apk add --no-cache build-base linux-headers musl-dev libffi-dev openssl-dev

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev && rm -rf ~/.cache

COPY . .

FROM python:3.13-alpine AS runtime

WORKDIR /app

RUN apk add --no-cache libffi openssl ca-certificates && \
    adduser -D -u 1000 appuser

COPY --from=build --chown=appuser:appuser /app /app

USER appuser
ENV PATH="/app/.venv/bin:$PATH" HOME=/home/appuser

CMD ["python", "main.py"]
