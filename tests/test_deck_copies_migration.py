import sqlite3
from pathlib import Path

import pytest

from scripts.migrate_sqlite_to_postgres import TABLE_ORDER, IDENTITY_TABLES, migrate_table
from scripts.verify_integrity import CHECKS
from test_deck_codes_permissions_migration import database


def migrated():
    db = database()
    db.commit()
    db.execute('PRAGMA foreign_keys=ON')
    sql = Path('migrations/0027_orange_deck_copies.sql').read_text('utf8')
    db.executescript(sql)
    db.executescript(sql)
    return db


def test_copy_migration_preserves_decks_and_enforces_unique_windows():
    db = migrated()
    assert db.execute('SELECT COUNT(*) FROM orange_decks').fetchone()[0] == 1
    assert db.execute('SELECT COUNT(*) FROM orange_deck_copies').fetchone()[0] == 0
    db.execute("INSERT INTO orange_deck_copies VALUES(1,'user:1','window1','now')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO orange_deck_copies VALUES(1,'user:1','window1','later')")
    db.execute("INSERT INTO orange_deck_copies VALUES(1,'user:1','window2','later')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO orange_deck_copies VALUES(99,'user:1','window1','now')")
    assert db.execute(dict(CHECKS)['deck copies reference orange_decks']).fetchone()[0] == 0
    db.commit()
    db.execute('PRAGMA foreign_keys=OFF')
    db.execute("INSERT INTO orange_deck_copies VALUES(99,'user:1','window1','now')")
    assert db.execute(dict(CHECKS)['deck copies reference orange_decks']).fetchone()[0] == 1


def test_import_preserves_copy_keys_and_windows_without_identity_reset():
    assert TABLE_ORDER.index('orange_decks') < TABLE_ORDER.index('orange_deck_copies')
    assert 'orange_deck_copies' not in IDENTITY_TABLES
    db = migrated()
    db.execute("INSERT INTO orange_deck_copies VALUES(1,'user:1','window1','now')")
    class Cursor:
        def executemany(self, sql, rows):
            self.sql, self.rows = sql, rows
        def execute(self, *args):
            pytest.fail('Composite primary keys have no identity sequence')
    cursor = Cursor()
    assert migrate_table(db, cursor, 'orange_deck_copies') == 1
    assert cursor.rows == [(1, 'user:1', 'window1', 'now')]
