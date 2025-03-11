#!/bin/bash

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd src/dispatch/static/dispatch
rm -rf node_modules package-lock.json
export NODE_OPTIONS="--max-old-space-size=4096"
npm install --legacy-peer-deps

# Run database migrations
cd /workspace
alembic upgrade head

export LOG_LEVEL="ERROR"
export STATIC_DIR="/static"
export DATABASE_HOSTNAME="db"
export DATABASE_CREDENTIALS="dispatch:dispatch"
export DISPATCH_ENCRYPTION_KEY="NJHDWDJ3PbHT8h"
export DISPATCH_JWT_SECRET="foo"

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h db -p 5432 -U dispatch; do
  sleep 1
done

# Restore sample data if file exists
if [ -f "/workspace/data/dispatch-sample-data.dump" ]; then
  dispatch database restore --dump-file /workspace/data/dispatch-sample-data.dump
fi

dispatch database upgrade
