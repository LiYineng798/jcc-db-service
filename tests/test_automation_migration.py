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
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO automation_imports VALUES (2,'batch-key','hash','{}','today')")
    assert TABLE_ORDER.index('users') < TABLE_ORDER.index('automation_accounts') < TABLE_ORDER.index('automation_imports')
    assert not {'automation_accounts', 'automation_imports'} & IDENTITY_TABLES
    for label, query in CHECKS:
        if label.startswith(('automation ', 'deleted automation')):
            assert db.execute(query).fetchone()[0] == 0
