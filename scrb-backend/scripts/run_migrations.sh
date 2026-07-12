#!/bin/bash
set -e

# Load environment variables from .env if present in current directory or parent
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ../.env ]; then
  export $(grep -v '^#' ../.env | xargs)
fi

# Fallback DATABASE_URL if not set
DATABASE_URL=${DATABASE_URL:-"postgresql+psycopg://scrb_user:scrb_pass@localhost:5432/scrb_dev"}

echo "Waiting for postgres database to be healthy..."
until python -c "
import sys, sqlalchemy
try:
    engine = sqlalchemy.create_engine('${DATABASE_URL}')
    with engine.connect() as conn:
        pass
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "Postgres is not ready yet - sleeping"
  sleep 1
done

echo "Database connected successfully"

echo "Running migrations..."
alembic upgrade head
