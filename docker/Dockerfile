FROM python:3.11.10-slim-bullseye AS sdist

LABEL maintainer="oss@netflix.com"
LABEL org.opencontainers.image.title="Dispatch PyPI Wheel"
LABEL org.opencontainers.image.description="PyPI Wheel Builder for Dispatch"
LABEL org.opencontainers.image.url="https://dispatch.io/"
LABEL org.opencontainers.image.source="https://github.com/netflix/dispatch"
LABEL org.opencontainers.image.vendor="Netflix, Inc."
LABEL org.opencontainers.image.authors="oss@netflix.com"

SHELL ["/bin/bash", "-o", "pipefail", "-o", "errexit", "-c"]

# Set BLIS environment variables for ARM compatibility
ENV BLIS_ARCH="generic"
ENV BLIS_COMPILER="gcc"
ENV BLIS_ENABLE_CBLAS="1"

# Get and set up Node for front-end asset building
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  wget \
  gcc g++ python3-dev libffi-dev libssl-dev make \
  libblas-dev liblapack-dev \
  && rm -rf /var/lib/apt/lists/*

RUN wget --quiet -O - https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs --no-install-recommends

ARG SOURCE_COMMIT
ENV DISPATCH_BUILD=${SOURCE_COMMIT:-unknown}
LABEL org.opencontainers.image.revision=$SOURCE_COMMIT
LABEL org.opencontainers.image.licenses="https://github.com/netflix/dispatch/blob/${SOURCE_COMMIT:-main}/LICENSE"

ARG DISPATCH_LIGHT_BUILD
ENV DISPATCH_LIGHT_BUILD=${DISPATCH_LIGHT_BUILD}

COPY . /usr/src/dispatch/
RUN YARN_CACHE_FOLDER="$(mktemp -d)" \
  && export YARN_CACHE_FOLDER \
  && pushd /usr/src/dispatch \
  && python setup.py bdist_wheel \
  && rm -r "$YARN_CACHE_FOLDER" \
  && mv /usr/src/dispatch/dist /dist

FROM python:3.11.10-slim-bullseye

LABEL maintainer="oss@dispatch.io"
LABEL org.opencontainers.image.title="Dispatch"
LABEL org.opencontainers.image.description="Dispatch runtime image"
LABEL org.opencontainers.image.url="https://github.com/netflix/dispatch"
LABEL org.opencontainers.image.documentation="https://github.com/netflix/dispatch"
LABEL org.opencontainers.image.source="https://github.com/netflix/dispatch"
LABEL org.opencontainers.image.vendor="Netflix, Inc."
LABEL org.opencontainers.image.authors="oss@netflix.com"

SHELL ["/bin/bash", "-o", "pipefail", "-o", "errexit", "-c"]

RUN groupadd -r dispatch && useradd -r -m -g dispatch dispatch

ENV PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  DISPATCH_CONF=/etc/dispatch \
  BLIS_ARCH="generic" \
  BLIS_COMPILER="gcc" \
  BLIS_ENABLE_CBLAS="1"

# Install base dependencies including gcc and development libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  wget \
  gnupg \
  gcc g++ \
  python3-dev \
  libffi-dev \
  libssl-dev \
  make \
  libblas-dev \
  liblapack-dev \
  && rm -rf /var/lib/apt/lists/*

RUN echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
  && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN wget --quiet -O - https://deb.nodesource.com/setup_20.x | bash -

COPY --from=sdist /dist/*.whl /tmp/dist/
RUN buildDeps="" \
  && apt-get update \
  && apt-get install -y --no-install-recommends "$buildDeps" \
  && apt-get install -y --no-install-recommends \
  pkg-config postgresql-client-14 nodejs \
  && pip install -U /tmp/dist/*.whl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /mjml_install \
  && cd /mjml_install \
  && npm install --no-cache-dir mjml \
  && mv node_modules / \
  && cd / \
  && rm -rf /mjml_install

EXPOSE 8000
VOLUME /var/lib/dispatch/files

ENTRYPOINT ["dispatch"]
CMD ["server", "start", "dispatch.main:app", "--host=0.0.0.0"]
