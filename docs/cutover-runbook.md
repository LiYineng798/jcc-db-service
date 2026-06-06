# SQLite to PostgreSQL Cutover Runbook

This runbook targets a low-risk first cutover from the current SQLite-backed Web service to a single Web instance backed by PostgreSQL.

## Pre-Cutover

1. Confirm current service health:

```bash
curl -fsS https://jcc.np5.top/api/health
systemctl status jcc --no-pager
```

2. Back up SQLite:

```bash
mkdir -p /opt/jcc/backups
cp /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  "/opt/jcc/backups/lineups.pre-postgres.$(date +%Y%m%d-%H%M%S).sqlite3"
```

3. Back up runtime files:

```bash
tar -czf "/opt/jcc/backups/instance.pre-postgres.$(date +%Y%m%d-%H%M%S).tar.gz" \
  -C /opt/jcc/jcc_git instance
```

4. Install and start PostgreSQL if not already installed.

5. Apply schema migrations:

```bash
cd /opt/jcc/jcc-db-service
. .venv/bin/activate
python scripts/apply_migrations.py \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"
```

6. Run initial import without touching production service:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc" \
  --truncate-target
```

7. Verify counts and integrity:

```bash
python scripts/verify_counts.py \
  --sqlite-path /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"

python scripts/verify_integrity.py \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"
```

## Final Cutover Window

SQLite has no built-in continuous replication to PostgreSQL, so use a short controlled write freeze.

1. Announce maintenance or choose a low-traffic window.

2. Stop Web writes by stopping the Web service:

```bash
systemctl stop jcc
```

3. Take final SQLite backup:

```bash
cp /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  "/opt/jcc/backups/lineups.final-sqlite.$(date +%Y%m%d-%H%M%S).sqlite3"
```

4. Re-import final SQLite into PostgreSQL:

```bash
cd /opt/jcc/jcc-db-service
. .venv/bin/activate
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc" \
  --truncate-target
```

5. Verify:

```bash
python scripts/verify_counts.py \
  --sqlite-path /opt/jcc/jcc_git/instance/lineups.sqlite3 \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"

python scripts/verify_integrity.py \
  --database-url "postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc"
```

6. Update `/etc/jcc.env` to include:

```text
JCC_DATABASE_URL=postgresql://jcc_app:replace-with-strong-password@database.np5.top:5432/jcc
```

7. Start Web service:

```bash
systemctl start jcc
```

8. Smoke test:

```bash
curl -fsS https://jcc.np5.top/api/health
```

Also test manually:

- homepage loads;
- login works;
- copy lineup works;
- like lineup works;
- favorite lineup works;
- admin overview loads.

## Rollback

If cutover verification fails:

1. Stop Web:

```bash
systemctl stop jcc
```

2. Remove or comment `JCC_DATABASE_URL` from `/etc/jcc.env`.

3. Restore final SQLite backup if needed:

```bash
cp /opt/jcc/backups/lineups.final-sqlite.YYYYMMDD-HHMMSS.sqlite3 \
  /opt/jcc/jcc_git/instance/lineups.sqlite3
chown jcc:jcc /opt/jcc/jcc_git/instance/lineups.sqlite3
```

4. Start Web:

```bash
systemctl start jcc
curl -fsS https://jcc.np5.top/api/health
```

Keep PostgreSQL data intact for investigation. Do not delete it during rollback.

