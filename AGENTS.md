# Repository Guidelines

This is the database service repository for the JCC workspace. It owns PostgreSQL schema migrations, SQLite-to-PostgreSQL import tooling, integrity checks, backups, restores, and database operations runbooks.

The sibling `..\jcc-web-service` repository owns Flask routes, Web/API behavior, frontend assets, account permissions, live comp display, admin UI, guestbook, patch notes, and Web-side database adapters. Do not edit Web-service files from this repository.

The parent `..\` directory is only a local coordination workspace and may also contain delivery artifacts such as `.sqlite3`, `.tar`, `.bundle`, or worktree files. Do not use the parent repository for normal feature commits.

For database changes, add SQL migrations under `migrations/` and focused tests under `tests/`. If Web code depends on the DB change, commit and deploy this repository first, then update `jcc-web-service`.

Migration `0009_live_comp_upload_jobs.sql` adds the administrator live-comp JSON upload job queue. It must remain schema-compatible with the Web service's SQLite `live_comp_upload_jobs` table in `db_schema.py`/`db_migrations.py`, including status/progress fields, result/error JSON, creator, and timestamps. The Web worker claims queued rows conditionally, so the indexes on `(status, created_at)` and `(created_by, created_at DESC)` are required for polling and audit views.
