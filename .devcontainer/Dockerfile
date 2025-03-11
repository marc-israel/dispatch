FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

ENV PYTHONUNBUFFERED 1

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends nodejs \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    curl \
    git \
    libffi-dev \
    python3-dev \
    pkg-config \
    libssl-dev \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install global npm packages
RUN npm install -g yarn mjml cross-env

# Configure npm for ARM64
ENV ROLLUP_SKIP_NATIVES=true \
    npm_config_arch=arm64 \
    npm_config_platform=darwin

# [Optional] Create a venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip

# Set development environment variables
ENV NODE_ENV=development \
    PYTHONPATH=/workspace \
    DISPATCH_CONF=/workspace/dispatch.conf

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>
