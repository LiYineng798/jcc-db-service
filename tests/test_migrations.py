from pathlib import Path


def test_initial_migration_defines_schema_migrations_table():
    sql = Path('migrations/0001_initial_schema.sql').read_text(encoding='utf-8')

    assert 'CREATE TABLE IF NOT EXISTS schema_migrations' in sql
    assert 'version TEXT PRIMARY KEY' in sql


def test_initial_migration_contains_current_business_tables():
    sql = Path('migrations/0001_initial_schema.sql').read_text(encoding='utf-8')

    for table in [
        'users',
        'lineups',
        'likes',
        'copy_events',
        'copy_action_events',
        'live_comp_global_stats',
        'live_comp_global_daily_stats',
        'cache_state',
        'app_settings',
        'favorites',
        'reports',
        'recent_lineup_views',
        'recent_lineup_copies',
        'login_events',
        'visit_events',
        'audit_logs',
        'rate_limits',
        'growth_events',
        'guestbook_messages',
        'patch_notes',
    ]:
        assert f'CREATE TABLE IF NOT EXISTS {table}' in sql


def test_seed_migration_uses_postgres_conflict_handling():
    sql = Path('migrations/0002_seed_defaults.sql').read_text(encoding='utf-8')

    assert 'ON CONFLICT (cache_key) DO NOTHING' in sql
    assert 'ON CONFLICT (setting_key) DO NOTHING' in sql


def test_site_notice_migration_preserves_existing_notice_data():
    sql = Path('migrations/0003_site_notices.sql').read_text(encoding='utf-8')

    assert 'CREATE TABLE IF NOT EXISTS site_notices' in sql
    assert 'idx_site_notices_single_active' in sql
    assert 'notice_data' in sql
    assert 'notice_enabled' in sql


def test_daily_report_migration_defines_report_snapshot_table():
    sql = Path('migrations/0007_daily_reports.sql').read_text(encoding='utf-8')

    assert 'CREATE TABLE IF NOT EXISTS daily_admin_reports' in sql
    assert 'report_date TEXT PRIMARY KEY' in sql
    assert 'unique_visitors INTEGER NOT NULL DEFAULT 0' in sql
    assert 'page_visits INTEGER NOT NULL DEFAULT 0' in sql
    assert 'successful_copies INTEGER NOT NULL DEFAULT 0' in sql
    assert 'payload_json TEXT NOT NULL' in sql
    assert 'generated_at TEXT NOT NULL' in sql
    assert 'updated_at TEXT NOT NULL' in sql
    assert 'idx_daily_admin_reports_generated_at' in sql


def test_visit_ip_migration_adds_daily_report_probe_indexes():
    sql = Path('migrations/0008_visit_ip_index.sql').read_text(encoding='utf-8')

    assert 'CREATE INDEX IF NOT EXISTS idx_visit_events_ip_date' in sql
    assert 'CREATE INDEX IF NOT EXISTS idx_copy_action_events_ip_created_at' in sql
