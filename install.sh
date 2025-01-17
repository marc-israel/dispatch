#!/bin/bash
set -e

# Install Python 3.11 if not already installed
brew install python@3.11

# Create symlinks for Python 3.11
brew link python@3.11

# Install build dependencies
brew install gcc openssl libffi

# Upgrade pip first
python3.11 -m pip install --upgrade pip

# Install and start PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Wait for PostgreSQL to start
sleep 5

# Create database and user
psql postgres -c "CREATE USER dispatch WITH PASSWORD 'dispatch' CREATEDB;"
createdb -U dispatch dispatch

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Set required environment variables
export LOG_LEVEL="ERROR"
export STATIC_DIR=""
export DATABASE_HOSTNAME="localhost"
export DATABASE_CREDENTIALS="dispatch:dispatch"
export DISPATCH_ENCRYPTION_KEY="NJHDWDJ3PbHT8h"
export DISPATCH_JWT_SECRET="foo"
export DISPATCH_LIGHT_BUILD=1

# Install Python dependencies
pip3 install --upgrade setuptools wheel

# Install scipy with a compatible version
pip3 install scipy==1.10.1

# Install psycopg2-binary first
pip3 install psycopg2-binary==2.9.9

# Install dispatch with specific version
pip3 install -e ".[dev]"

# Install database
dispatch database restore --dump-file data/dispatch-sample-data.dump
dispatch database upgrade

# Install plugins
dispatch plugins install

echo "Installation complete!"
