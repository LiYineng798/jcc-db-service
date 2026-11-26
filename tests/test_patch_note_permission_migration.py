import sqlite3
from pathlib import Path

import pytest


def test_existing_and_new_accounts_start_without_patch_note_access():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE automation_accounts (user_id INTEGER PRIMARY KEY)')
    db.execute('INSERT INTO automation_accounts VALUES (1)')
    db.executescript(Path('migrations/0032_automation_patch_notes.sql').read_text(encoding='utf8'))
    db.execute('INSERT INTO automation_accounts (user_id) VALUES (2)')
    assert db.execute('SELECT patch_note_access FROM automation_accounts').fetchall() == [('none',), ('none',)]
    for access in ('draft', 'publish'):
        db.execute('UPDATE automation_accounts SET patch_note_access=?', (access,))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE automation_accounts SET patch_note_access='admin'")
