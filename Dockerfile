FROM python:3.13-slim

# Install uv and curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install opencode CLI
RUN curl -fsSL https://opencode.ai/install | bash

# Set working directory
WORKDIR /app

# Copy current directory contents into the container at /app
ADD . /app