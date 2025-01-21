# Build stage
FROM --platform=$BUILDPLATFORM python:3.11.10-slim-bullseye AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  libffi-dev \
  libpq-dev \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js for ARM64
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g yarn

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
  wheel \
  setuptools \
  "pydantic<2.0" \
  "fastapi<0.100.0" \
  sqlalchemy \
  sqlalchemy-utils \
  alembic \
  psycopg2-binary \
  bcrypt \
  python-slugify \
  python-jose[cryptography] \
  python-multipart \
  email-validator \
  markdown \
  setuptools_scm

# Set up frontend build environment
WORKDIR /build/src/dispatch/static/dispatch

# Create .npmrc to skip optional dependencies
RUN echo "optional=false" > .npmrc \
  && echo "FORMKIT_ENTERPRISE_TOKEN=none" > .env

# Clean any existing node_modules
RUN rm -rf node_modules package-lock.json

# Install frontend dependencies
RUN npm install \
  && npm install -D vite@latest \
  && npm install -D @vitejs/plugin-vue@latest \
  && npm install -D rollup@latest \
  && npm install -D @vue/compiler-sfc \
  && npm install -D sass

# Ensure vite is in PATH and set NODE_ENV
ENV PATH="/build/src/dispatch/static/dispatch/node_modules/.bin:${PATH}" \
  NODE_ENV=production

# Build frontend assets
RUN npm run build

# Build wheel
WORKDIR /build
RUN echo "0.1.0" > VERSION \
  && SETUPTOOLS_SCM_PRETEND_VERSION="0.1.0" \
  FORMKIT_ENTERPRISE_TOKEN=none \
  python setup.py bdist_wheel

# Runtime stage
FROM --platform=$BUILDPLATFORM python:3.11.10-slim-bullseye

WORKDIR /app

# Install runtime dependencies including build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  gnupg \
  libpq5 \
  gcc \
  build-essential \
  libffi-dev \
  libssl-dev \
  python3-dev \
  pkg-config \
  && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
  && echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  postgresql-client-14 \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd -r dispatch \
  && useradd -r -g dispatch -d /app dispatch \
  && chown -R dispatch:dispatch /app

# Install Node.js (needed for runtime)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g mjml \
  && rm -rf /var/lib/apt/lists/*

# Copy wheel from builder and install
COPY --from=builder /build/dist/*.whl /tmp/dist/
RUN buildDeps="gcc build-essential libffi-dev libssl-dev python3-dev pkg-config" \
  && apt-get update \
  && apt-get install -y --no-install-recommends $buildDeps \
  && apt-get install -y --no-install-recommends \
  gcc \
  build-essential \
  libffi-dev \
  libssl-dev \
  python3-dev \
  pkg-config \
  # remove internal index when internal plugins are separated
  && pip install -U /tmp/dist/*.whl \
  && apt-get purge -y --auto-remove "$buildDeps" \
  && apt-get install -y --no-install-recommends \
  pkg-config \
  postgresql-client-14 \
  nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /mjml_install \
  && cd /mjml_install \
  && npm install --no-cache-dir mjml \
  && mv node_modules / \
  && cd / \
  && rm -rf /mjml_install

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
  DISPATCH_CONF=/etc/dispatch \
  NODE_OPTIONS="--max-old-space-size=4096"

USER dispatch

EXPOSE 8000
VOLUME /var/lib/dispatch/files

ENTRYPOINT ["dispatch"]
CMD ["server", "start", "dispatch.main:app", "--host=0.0.0.0"]
