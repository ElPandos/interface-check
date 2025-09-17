# ------------------ Stage: build ------------------ #
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build

WORKDIR /app

# Build dependencies for C-extensions
RUN apk add --no-cache \
    build-base \
    linux-headers \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy dependency files first
COPY pyproject.toml uv.lock* ./

# Install production dependencies only
RUN uv sync --frozen --no-dev \
    && rm -rf ~/.cache

# Copy app source code
COPY . .

# ------------------ Stage: runtime ------------------ #
FROM python:3.13-alpine AS runtime

WORKDIR /app

# Runtime-only libraries
RUN apk add --no-cache \
    libffi \
    openssl \
    ca-certificates

# Copy virtualenv & app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app /app

# Non-root user
RUN adduser -D -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
ENV HOME=/home/appuser

# Default entrypoint
CMD ["python", "main.py"]
