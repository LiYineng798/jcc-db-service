from pathlib import Path

import pytest
import sqlite3

from test_deck_codes_permissions_migration import database
from scripts.migrate_sqlite_to_postgres import migrate_table


def upgraded_database():
    db = database()
    db.execute("UPDATE orange_decks SET plan_code='方案-大橘大利-MQ=='")
    db.executescript(Path('migrations/0028_orange_deck_lineup_code.sql').read_text(encoding='utf-8'))
    return db


def test_upgrade_preserves_plan_and_defaults_lineup_to_empty():
    db = upgraded_database()
    assert tuple(db.execute('SELECT name,plan_code,lineup_code FROM orange_decks').fetchone()) == (
        '旧卡组', '方案-大橘大利-MQ==', '')
    db.execute("UPDATE orange_decks SET lineup_code='#ABC123'")
    assert tuple(db.execute('SELECT plan_code,lineup_code FROM orange_decks').fetchone()) == (
        '方案-大橘大利-MQ==', '#ABC123')
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('UPDATE orange_decks SET lineup_code=NULL')


def test_sqlite_import_transfers_both_codes():
    db = upgraded_database()
    db.execute("UPDATE orange_decks SET lineup_code='#ABC123'")
    captured = {}

    class Cursor:
        def executemany(self, sql, rows):
            captured['sql'], captured['rows'] = sql, rows

        def execute(self, *args):
            pass

        def fetchone(self):
            return (1,)

    assert migrate_table(db, Cursor(), 'orange_decks') == 1
    assert '"lineup_code"' in captured['sql']
    assert '#ABC123' in captured['rows'][0]
    assert '方案-大橘大利-MQ==' in captured['rows'][0]
