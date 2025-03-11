# Build stage
FROM --platform=linux/arm64 python:3.11.10-slim-bullseye AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  libffi-dev \
  libpq-dev \
  python3-dev \
  pkg-config \
  libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js specifically for ARM64
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g yarn \
  && npm config set registry https://registry.npmjs.org/

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
  setuptools_scm \
  uvicorn

# Set up frontend build environment
WORKDIR /build/src/dispatch/static/dispatch

# Create .npmrc to skip optional dependencies
RUN echo "optional=false" > .npmrc \
  && echo "FORMKIT_ENTERPRISE_TOKEN=none" > .env

# Clean any existing node_modules
RUN rm -rf node_modules package-lock.json

# Update axios version to be compatible with @vueuse/integrations
RUN npm install axios@^1.0.0 --save --legacy-peer-deps

# Install frontend dependencies
ARG NPM_FLAGS=""
RUN npm install ${NPM_FLAGS} \
  && npm install -D vite@5.0.0 ${NPM_FLAGS} \
  && npm install -D @vitejs/plugin-vue@5.0.0 ${NPM_FLAGS} \
  && npm install -D vite-plugin-vuetify@^2.0.1 ${NPM_FLAGS} \
  && npm install -D rollup@4.9.0 ${NPM_FLAGS} \
  && npm install -D @vue/compiler-sfc ${NPM_FLAGS} \
  && npm install -D sass ${NPM_FLAGS}

# Ensure vite is in PATH and set NODE_ENV
ENV PATH="/build/src/dispatch/static/dispatch/node_modules/.bin:${PATH}" \
  NODE_ENV=production \
  ROLLUP_SKIP_NATIVES=true \
  VITE_CJS_IGNORE_WARNING=true

# Build frontend assets
RUN NODE_OPTIONS=--max_old_space_size=4096 npm run build

# Build wheel
WORKDIR /build
RUN echo "0.1.0" > VERSION \
  && SETUPTOOLS_SCM_PRETEND_VERSION="0.1.0" \
  && sed -i 's/\["npm", "install"\]/\["npm", "install", "--legacy-peer-deps"\]/' setup.py \
  && sed -i 's/\["npm", "run", "build"\]/\["npm", "run", "build", "--force"\]/' setup.py \
  && FORMKIT_ENTERPRISE_TOKEN=none \
  python setup.py bdist_wheel

# Runtime stage
FROM --platform=linux/arm64 python:3.11.10-slim-bullseye

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
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
  DISPATCH_CONF=/etc/dispatch \
  NODE_OPTIONS="--max-old-space-size=4096"

USER dispatch

EXPOSE 8000
VOLUME /var/lib/dispatch/files

ENTRYPOINT ["dispatch"]
CMD ["server", "start", "dispatch.main:app", "--host=0.0.0.0"]
