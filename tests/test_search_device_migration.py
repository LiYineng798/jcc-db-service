from pathlib import Path
from scripts.migrate_sqlite_to_postgres import TABLE_ORDER, IDENTITY_TABLES
from scripts.verify_integrity import CHECKS


def test_search_device_migration_preserves_history_and_has_import_and_integrity_coverage():
    sql=Path('migrations/0017_search_device_analytics.sql').read_text(encoding='utf-8')
    assert sql.count("ADD COLUMN IF NOT EXISTS device_type TEXT NOT NULL DEFAULT 'unknown'")==2
    assert 'UPDATE visit_events' not in sql and 'UPDATE copy_action_events' not in sql
    assert 'UNIQUE(visitor_key, event_id)' in sql
    assert 'CHECK (result_count >= 0)' in sql
    assert 'ON search_events(created_at)' in sql and 'ON visit_events(created_at)' in sql
    assert TABLE_ORDER.index('users')<TABLE_ORDER.index('search_events')
    assert 'search_events' in IDENTITY_TABLES
    assert any('search_events' in query for _,query in CHECKS)
