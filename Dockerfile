# Stage 1: Builder
FROM python:3.13-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.5 /uv /uvx /bin/

ADD . /app

WORKDIR /app

# Copy project definition files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --locked

# Stage 2: Runtime
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.5 /uv /uvx /bin/

# Set up working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set entrypoint
CMD ["uv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]