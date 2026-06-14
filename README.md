# JCC Database Service

PostgreSQL deployment, schema migrations, backups, and SQLite-to-PostgreSQL migration tooling for JCC.

Local start:

```bash
cp .env.example .env
docker compose up -d
python scripts/apply_migrations.py --database-url "$DATABASE_URL"
```

Production should restrict port `5432` to trusted Web service IPs only. Do not expose PostgreSQL broadly to the public internet.

