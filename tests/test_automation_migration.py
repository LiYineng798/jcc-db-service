import sqlite3
from pathlib import Path

import pytest

from scripts.migrate_sqlite_to_postgres import TABLE_ORDER, IDENTITY_TABLES
from scripts.verify_integrity import CHECKS


def test_machine_schema_constraints_and_import_order():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('CREATE TABLE users(id BIGINT PRIMARY KEY, role TEXT, status TEXT)')
    sql = Path('migrations/0023_automation_accounts.sql').read_text(encoding='utf-8')
    db.executescript(sql)
    db.executescript(sql)
    db.execute("INSERT INTO users VALUES (1,'admin','active'),(2,'automation','active')")
    insert = """INSERT INTO automation_accounts (user_id,token_hash,token_prefix,expires_at,created_by,can_import)
                VALUES (?, 'hash', 'prefix', '2026-11-01', 1, ?)"""
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(insert, (3, 0))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(insert, (2, 2))
    db.execute(insert, (2, 1))
    db.execute("INSERT INTO automation_imports VALUES (2,'batch-key','hash','{}','today')")
    db.executescript(Path('migrations/0024_automation_sessions.sql').read_text(encoding='utf-8'))
    assert db.execute('SELECT user_id, can_import, can_touch, session_version FROM automation_accounts').fetchone() == (2, 1, 0, 1)
    assert 'token_hash' not in [row[1] for row in db.execute('PRAGMA table_info(automation_accounts)')]
    assert not db.execute("SELECT name FROM sqlite_master WHERE name='automation_imports'").fetchone()
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('UPDATE automation_accounts SET can_touch=2')
    assert TABLE_ORDER.index('users') < TABLE_ORDER.index('automation_accounts')
    assert not {'automation_accounts', 'automation_imports'} & IDENTITY_TABLES
    for label, query in CHECKS:
        if label.startswith(('automation ', 'deleted automation')):
            assert db.execute(query).fetchone()[0] == 0


def test_import_legacy_accounts_discards_removed_credentials():
    from scripts.migrate_sqlite_to_postgres import migrate_table
    source = sqlite3.connect(':memory:')
    source.row_factory = sqlite3.Row
    source.execute('CREATE TABLE automation_accounts(user_id INTEGER,token_hash TEXT,token_prefix TEXT,can_import INTEGER)')
    source.execute("INSERT INTO automation_accounts VALUES(7,'secret','prefix',1)")
    target = sqlite3.connect(':memory:')
    target.execute('CREATE TABLE automation_accounts(user_id INTEGER,can_import INTEGER,can_touch INTEGER DEFAULT 0,session_version INTEGER DEFAULT 1)')
    class Cursor:
        def executemany(self, sql, rows):
            assert 'token' not in sql
            target.executemany(sql.replace('%s', '?'), rows)
    assert migrate_table(source, Cursor(), 'automation_accounts') == 1
    assert target.execute('SELECT * FROM automation_accounts').fetchone() == (7, 1, 0, 1)
