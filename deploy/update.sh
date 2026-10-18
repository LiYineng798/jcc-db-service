#!/usr/bin/env bash
set -euo pipefail

# Run only after the backup/maintenance steps in docs/operations.md.
: "${JCC_DB_ENV_FILE:?Set an absolute private environment file path}"
[[ "$JCC_DB_ENV_FILE" = /* && -r "$JCC_DB_ENV_FILE" ]] || {
    printf '%s\n' 'JCC_DB_ENV_FILE must be an absolute, readable file' >&2
    exit 1
}
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"
set -a
source "$JCC_DB_ENV_FILE"
set +a
: "${JCC_DATABASE_URL:?Set JCC_DATABASE_URL in the private environment file}"

git pull --ff-only origin main
source .venv/bin/activate
pip install -r requirements.txt
python scripts/apply_migrations.py --database-url "$JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"
echo "jcc-db-service update completed"
