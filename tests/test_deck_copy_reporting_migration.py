import sqlite3
from pathlib import Path

from scripts.migrate_sqlite_to_postgres import migrate_table

MIGRATION = Path('migrations/0029_deck_copy_reporting.sql').read_text(encoding='utf-8')


def database():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE copy_action_events (id INTEGER PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
            counted INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
        CREATE TABLE orange_deck_copies (deck_id INTEGER NOT NULL, copy_key TEXT NOT NULL, bucket_start TEXT NOT NULL,
            created_at TEXT NOT NULL, PRIMARY KEY (deck_id, copy_key, bucket_start));
        INSERT INTO copy_action_events (target_type, target_id, created_at) VALUES ('lineup', '1', 'now');
    ''')
    # SQLite lacks ADD COLUMN IF NOT EXISTS; PostgreSQL runs the file as written.
    db.executescript(MIGRATION.replace('ADD COLUMN IF NOT EXISTS', 'ADD COLUMN'))
    return db


def test_upgrade_keeps_history_with_null_code_type_and_indexes_copy_window():
    db = database()
    assert tuple(db.execute('SELECT target_type, code_type FROM copy_action_events').fetchone()) == ('lineup', None)
    db.execute("INSERT INTO copy_action_events (target_type, target_id, created_at, code_type) VALUES ('orange_deck', '7', 'now', 'lineup')")
    assert db.execute("SELECT code_type FROM copy_action_events WHERE target_type = 'orange_deck'").fetchone()[0] == 'lineup'
    plan = ' '.join(row[3] for row in db.execute(
        "EXPLAIN QUERY PLAN SELECT substr(bucket_start, 1, 10), deck_id, COUNT(*) FROM orange_deck_copies "
        "WHERE bucket_start >= '2026-01-01' GROUP BY substr(bucket_start, 1, 10), deck_id"))
    assert 'idx_orange_deck_copies_bucket' in plan


def test_migration_is_rerunnable_on_postgres_syntax():
    assert 'ADD COLUMN IF NOT EXISTS code_type' in MIGRATION and 'CREATE INDEX IF NOT EXISTS' in MIGRATION


def test_sqlite_import_transfers_code_type():
    db = database()
    db.execute("UPDATE copy_action_events SET code_type = 'plan', target_type = 'orange_deck'")
    captured = {}

    class Cursor:
        def executemany(self, sql, rows):
            captured['sql'], captured['rows'] = sql, rows

        def execute(self, *args):
            pass

        def fetchone(self):
            return (1,)

    assert migrate_table(db, Cursor(), 'copy_action_events') == 1
    assert '"code_type"' in captured['sql'] and 'plan' in captured['rows'][0]
