# JCC PostgreSQL Deployment

This service owns PostgreSQL deployment, migrations, backup, restore, and SQLite import tooling for JCC.

## Current Production Facts

- Database host: `103.23.148.85`, Debian 12.
- Database service path: `/opt/jcc/jcc-db-service`.
- PostgreSQL database: `jcc`.
- PostgreSQL app user: `jcc_app`.
- Secret env file: `/root/.jcc-db.env`.
- PostgreSQL service: `postgresql`.
- Firewall service: `nftables`.
- Backup directory: `/opt/jcc/postgres-backups`.
- Current Web host allowed to connect: `103.23.148.135`.
- Current Web app path: `/opt/jcc/jcc-web-service`.
- Old Web rollback path: `/opt/jcc/jcc_git`.

For daily operations, migrations, backups, restores, and cross-repository update
order, see [`operations.md`](operations.md).

## Recommended First Production Install

Use Debian PostgreSQL packages for the first deployment. This avoids adding Docker as a new production runtime dependency.

```bash
apt update
apt install -y postgresql postgresql-client
systemctl enable postgresql
systemctl start postgresql
```

Create database and app user:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE jcc;
CREATE USER jcc_app WITH PASSWORD 'replace-with-strong-password';
GRANT ALL PRIVILEGES ON DATABASE jcc TO jcc_app;
\c jcc
GRANT ALL ON SCHEMA public TO jcc_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO jcc_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO jcc_app;
```

Use this Web connection string shape after cutover:

```text
JCC_DATABASE_URL=postgresql://jcc_app:replace-with-strong-password@103.23.148.85:5432/jcc
```

## Network Safety

Do not expose PostgreSQL to the whole internet.

TCP `5432` should only be reachable from trusted Web server IPs.

Check listening ports:

```bash
ss -lntp
```

When adding or moving Web hosts, change PostgreSQL and firewall rules together:

```text
allow 5432 only from Web server public IPs or private network
```

## Apply Migrations

Install Python dependencies for this repository:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run migrations:

```bash
python scripts/apply_migrations.py \
  --database-url "$JCC_DATABASE_URL"
```

Verify:

```bash
sudo -u postgres psql -d jcc -c "\\dt"
```

## Backups

Create backup directory:

```bash
mkdir -p /opt/jcc/postgres-backups
chmod 700 /opt/jcc/postgres-backups
```

Manual backup:

```bash
set -a
. /root/.jcc-db.env
set +a
PGPASSWORD="$JCC_DB_PASSWORD" pg_dump \
  -h 127.0.0.1 \
  -U "$JCC_DB_USER" \
  -d "$JCC_DB_NAME" \
  -Fc \
  -f "/opt/jcc/postgres-backups/jcc.$(date +%Y%m%d-%H%M%S).dump"
```

Keep SQLite backups until PostgreSQL has served production traffic through at least one full traffic cycle.
