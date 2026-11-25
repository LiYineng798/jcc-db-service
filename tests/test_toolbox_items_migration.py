from pathlib import Path
import sqlite3

import pytest

from scripts import migrate_sqlite_to_postgres, verify_integrity

MIGRATION = Path(__file__).resolve().parents[1] / 'migrations' / '0031_toolbox_items.sql'


def test_toolbox_items_migration_constraints_and_tooling():
    sql = MIGRATION.read_text(encoding='utf-8').replace('BIGINT', 'INTEGER')
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY)')
    conn.execute('INSERT INTO users (id) VALUES (1)')
    conn.executescript(sql)

    conn.execute(
        '''
        INSERT INTO toolbox_items (tool_id, title, description, group_name, status, sort_order, updated_at, updated_by)
        VALUES ('golden-egg', '金蛋奖励', 'desc', 'S18', 'visible', 1, '2026-11-25 12:00:00', 1)
        '''
    )
    for bad_status in ('hidden', 'archived', ''):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                '''
                INSERT INTO toolbox_items (tool_id, title, status, sort_order, updated_at)
                VALUES ('bad', 'Bad', ?, 2, '2026-11-25 12:00:00')
                ''',
                (bad_status,),
            )

    assert 'toolbox_items' in migrate_sqlite_to_postgres.TABLE_ORDER
    assert migrate_sqlite_to_postgres.TABLE_ORDER.index('users') < migrate_sqlite_to_postgres.TABLE_ORDER.index('toolbox_items')
    assert any(label == 'toolbox_items.updated_by -> users.id' for label, _ in verify_integrity.CHECKS)
