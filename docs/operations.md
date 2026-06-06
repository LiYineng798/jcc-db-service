# JCC Database Operations

This repository is the source of truth for PostgreSQL schema migrations, data
imports, integrity checks, and database backup/restore tooling.

Web application code lives in `jcc-web-service`.

## Current Production Layout

| Item | Value |
|---|---|
| Database server | `103.23.148.85` |
| Database service directory | `/opt/jcc/jcc-db-service` |
| PostgreSQL database | `jcc` |
| PostgreSQL app user | `jcc_app` |
| PostgreSQL service | `postgresql` |
| Firewall service | `nftables` |
| Secret env file | `/root/.jcc-db.env` |
| Backup directory | `/opt/jcc/postgres-backups` |
| Web server allowed to connect | `103.23.148.135` |

Do not commit database passwords or SSH passwords.

## What This Repository Owns

- SQL migrations under `migrations/`.
- Migration runner: `scripts/apply_migrations.py`.
- SQLite to PostgreSQL import: `scripts/migrate_sqlite_to_postgres.py`.
- Count verification: `scripts/verify_counts.py`.
- Integrity verification: `scripts/verify_integrity.py`.
- Database deployment and cutover runbooks.

## Daily Database Update Workflow

Use this flow when a change adds or modifies tables, columns, indexes, seed data,
or database maintenance scripts.

Local development:

```powershell
cd D:\1\codex\jcc-new\jcc-db-service
git pull origin main
```

Add a migration file:

```text
migrations/0003_descriptive_name.sql
```

Run tests:

```powershell
python -m pytest -q
```

Commit and push:

```powershell
git add .
git commit -m "feat: add descriptive database migration"
git push origin main
```

Apply on the database server:

```bash
cd /opt/jcc/jcc-db-service
git pull origin main
. .venv/bin/activate
pip install -r requirements.txt
set -a
. /root/.jcc-db.env
set +a
python scripts/apply_migrations.py --database-url "$JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"
```

List applied migrations:

```bash
sudo -u postgres psql -d jcc -c "SELECT version FROM schema_migrations ORDER BY version;"
```

## Backup

Create a PostgreSQL dump before risky migrations:

```bash
set -a
. /root/.jcc-db.env
set +a
mkdir -p /opt/jcc/postgres-backups
chmod 700 /opt/jcc/postgres-backups
PGPASSWORD="$JCC_DB_PASSWORD" pg_dump \
  -h 127.0.0.1 \
  -U "$JCC_DB_USER" \
  -d "$JCC_DB_NAME" \
  -Fc \
  -f "/opt/jcc/postgres-backups/jcc.$(date +%Y%m%d-%H%M%S).dump"
```

Check recent backups:

```bash
ls -lh /opt/jcc/postgres-backups | tail
```

## Restore

Restores can overwrite production data. Stop the Web service first unless this is
a restore into a separate test database.

```bash
# On the Web server:
systemctl stop jcc
```

Then on the database server:

```bash
set -a
. /root/.jcc-db.env
set +a
sudo -u postgres dropdb "$JCC_DB_NAME"
sudo -u postgres createdb -O "$JCC_DB_USER" "$JCC_DB_NAME"
PGPASSWORD="$JCC_DB_PASSWORD" pg_restore \
  -h 127.0.0.1 \
  -U "$JCC_DB_USER" \
  -d "$JCC_DB_NAME" \
  --clean \
  --if-exists \
  /opt/jcc/postgres-backups/jcc.YYYYMMDD-HHMMSS.dump
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"
```

Restart Web after verification:

```bash
# On the Web server:
systemctl start jcc
curl -fsS http://127.0.0.1:5000/api/health
```

## SQLite Import

Use this only for controlled re-imports from an old SQLite snapshot.

```bash
cd /opt/jcc/jcc-db-service
. .venv/bin/activate
set -a
. /root/.jcc-db.env
set +a
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /opt/jcc/postgres-backups/lineups.final-sqlite.YYYYMMDD-HHMMSS.sqlite3 \
  --database-url "$JCC_DATABASE_URL" \
  --truncate-target
python scripts/verify_counts.py \
  --sqlite-path /opt/jcc/postgres-backups/lineups.final-sqlite.YYYYMMDD-HHMMSS.sqlite3 \
  --database-url "$JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"
```

Do not use `--truncate-target` while the Web service is accepting writes.

## Connectivity And Firewall

PostgreSQL should only be reachable from trusted Web servers.

Check PostgreSQL:

```bash
systemctl is-active postgresql
ss -lntp | grep 5432
```

Check `pg_hba.conf`:

```bash
grep -n 'jcc_app' /etc/postgresql/15/main/pg_hba.conf
```

Check nftables:

```bash
systemctl is-active nftables
nft list ruleset
```

Current intended rule:

```text
allow 103.23.148.135 -> tcp/5432
drop other tcp/5432
```

If a new Web server is added, add its source IP to both `pg_hba.conf` and the
firewall rules, then restart/reload the services.

## Cross-Repository Deployment Order

When a release includes both database and Web changes:

1. Deploy this repository first.
2. Apply migrations.
3. Run integrity verification.
4. Deploy `jcc-web-service`.
5. Restart `jcc.service`.
6. Run Web smoke tests.

This keeps the database schema ahead of Web code that depends on it.
