"""Exercise portable SQL constraints; production PostgreSQL migration is run at deployment."""
import sqlite3
from pathlib import Path

import pytest

from scripts.migrate_sqlite_to_postgres import TABLE_ORDER, IDENTITY_TABLES
from scripts.verify_integrity import CHECKS


def test_release_migration_constraints_and_idempotency():
    db=sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('CREATE TABLE users(id INTEGER PRIMARY KEY)')
    sql=Path('migrations/0015_season_release_packages.sql').read_text('utf8')
    db.executescript(sql)
    db.executescript(sql)
    insert='''INSERT INTO season_release_packages(id,package_id,season_id,game_version,data_revision,zip_sha256,
              filename,total_bytes,state,manifest_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)'''
    values=('r1','p1','s18','18.18.2',1,'sha1','p.zip',10,'queued','{}','2026-09-10')
    db.execute(insert,values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(insert,('r2','p2',*values[2:5],'sha2',*values[6:]))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO season_active_releases(season_id,release_id,updated_at) VALUES ('s18','missing','today')")
    assert TABLE_ORDER.index('users') < TABLE_ORDER.index('season_release_packages') < TABLE_ORDER.index('season_import_jobs')
    assert all(name not in IDENTITY_TABLES for name in ('season_release_packages','season_import_jobs','season_release_events'))
    assert db.execute(CHECKS[2][1]).fetchone()[0]==1
    db.execute("INSERT INTO season_import_jobs(id,release_id,status,created_at,updated_at) VALUES ('r1','r1','queued','today','today')")
    assert db.execute(CHECKS[2][1]).fetchone()[0]==0
    db.execute("INSERT INTO season_active_releases(season_id,release_id,updated_at) VALUES ('s18','r1','today')")
    assert db.execute(CHECKS[0][1]).fetchone()[0]==1
    db.execute("UPDATE season_release_packages SET state='ready',published_at='today' WHERE id='r1'")
    assert db.execute(CHECKS[0][1]).fetchone()[0]==0
    db.close()
