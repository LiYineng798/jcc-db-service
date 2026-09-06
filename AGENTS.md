# Repository Guidelines

Migration `0014_user_avatars.sql` adds `users.avatar_color`, backfills existing users with random system colors, and enforces a six-digit hexadecimal color. Apply it before deploying Web avatar support. Existing SQLite imports without this field use the default color; imports with the field preserve it. Only colors are stored; fixed SVG geometry belongs to the Web service. Do not store image uploads or runtime image blobs for this feature.

This is the database service repository for the JCC workspace. It owns PostgreSQL schema migrations, SQLite-to-PostgreSQL import tooling, integrity checks, backups, restores, and database operations runbooks.

The sibling `..\jcc-web-service` repository owns Flask routes, Web/API behavior, frontend assets, account permissions, live comp display, admin UI, guestbook, patch notes, and Web-side database adapters. Do not edit Web-service files from this repository.

The parent `..\` directory is only a local coordination workspace and may also contain delivery artifacts such as `.sqlite3`, `.tar`, `.bundle`, or worktree files. Do not use the parent repository for normal feature commits.

For database changes, add SQL migrations under `migrations/` and focused tests under `tests/`. If Web code depends on the DB change, commit and deploy this repository first, then update `jcc-web-service`.

Migration `0009_live_comp_upload_jobs.sql` adds the administrator live-comp JSON upload job queue. It must remain schema-compatible with the Web service's SQLite `live_comp_upload_jobs` table in `db_schema.py`/`db_migrations.py`, including status/progress fields, result/error JSON, creator, and timestamps. The Web worker claims queued rows conditionally, so the indexes on `(status, created_at)` and `(created_by, created_at DESC)` are required for polling and audit views.

Migration `0010_audit_target_key.sql` adds the text `audit_logs.target_key` column and index. Numeric entity IDs continue using `target_id`; seasons, dates, UUID jobs, and composite identifiers use `target_key`. Keep this migration aligned with the Web SQLite backfill and audit serializer before deploying Web code that writes text targets.

Migration `0011_live_comp_copy_dedup.sql` adds `live_comp_copy_events`, the five-minute effective-copy claim table for real-time lineups. Its unique key is `(season_id, live_comp_id, copy_key, bucket_start)` so repeated actions remain visible in `copy_action_events` while only the first copy in a bucket increments public counters. Keep it aligned with the Web SQLite schema and backfill.

Migration `0013_guestbook_message_status.sql` adds read/archive workflow fields to `guestbook_messages`. The Web admin uses `unread`, `read`, and `archived` statuses, with nullable actor/timestamp fields and an index on `(status, created_at DESC)`.
