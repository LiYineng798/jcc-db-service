#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/jcc/jcc-db-service"
ENV_FILE="/root/.jcc-db.env"

cd "$PROJECT_DIR"

git fetch origin main
git reset --hard origin/main

source .venv/bin/activate
pip install -r requirements.txt

set -a
source "$ENV_FILE"
set +a

python scripts/apply_migrations.py --database-url "$JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"

echo "jcc-db-service update completed"
