# JCC PostgreSQL Deployment

This service owns PostgreSQL deployment, migrations, backup, restore, and SQLite import tooling for JCC.

## Current Production Facts

- Host: Debian Linux.
- Current Web app path: `/opt/jcc/jcc_git`.
- Current SQLite database: `/opt/jcc/jcc_git/instance/lineups.sqlite3`.
- Current runtime data directory: `/opt/jcc/jcc_git/instance`.
- Current Web service: `jcc.service`.
- Current Gunicorn bind: `0.0.0.0:5000`.
- Server currently has no Docker, `psql`, or `sqlite3` CLI installed.

## Recommended First Production Install

Use Debian PostgreSQL packages for the first deployment. This avoids adding Docker as a new production runtime dependency on the current server.

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

Use this Web connection string after cutover:

```text
JCC_DATABASE_URL=postgresql://jcc_app:replace-with-strong-password@database.np5.top:5432/jcc
```

## Network Safety

Do not expose PostgreSQL to the whole internet.

For the first phase, `database.np5.top` may point to the current server, but TCP `5432` should only be reachable from trusted Web server IPs. If Web and database are on the same server during phase one, keep PostgreSQL bound to localhost until remote Web instances are actually needed.

Check listening ports:

```bash
ss -lntp
```

For same-host phase-one deployment, prefer:

```text
listen_addresses = '127.0.0.1'
```

When moving the database to its own host later, change PostgreSQL and firewall rules together:

```text
listen_addresses = '*'
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
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"
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
PGPASSWORD='replace-with-strong-password' pg_dump \
  -h 127.0.0.1 \
  -U jcc_app \
  -d jcc \
  -Fc \
  -f "/opt/jcc/postgres-backups/jcc.$(date +%Y%m%d-%H%M%S).dump"
```

Keep SQLite backups until PostgreSQL has served production traffic through at least one full traffic cycle.

