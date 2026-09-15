#!/usr/bin/env bash
set -euo pipefail

# Run only after the backup/maintenance steps in docs/operations.md.

PROJECT_DIR="/opt/jcc/jcc-db-service"
ENV_FILE="${JCC_DB_ENV_FILE:-/etc/jcc.env}"

cd "$PROJECT_DIR"

git pull --ff-only origin main

source .venv/bin/activate
pip install -r requirements.txt

set -a
source "$ENV_FILE"
set +a

python scripts/apply_migrations.py --database-url "$JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"

echo "jcc-db-service update completed"
