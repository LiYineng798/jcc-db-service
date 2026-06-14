from scripts.migrate_sqlite_to_postgres import IDENTITY_TABLES, TABLE_ORDER


def test_table_order_loads_parent_tables_before_children():
    assert TABLE_ORDER.index('users') < TABLE_ORDER.index('lineups')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('likes')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('favorites')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('reports')


def test_table_order_includes_current_tables():
    assert TABLE_ORDER == [
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
    ]


def test_identity_tables_exclude_text_primary_key_tables():
    assert 'users' in IDENTITY_TABLES
    assert 'lineups' in IDENTITY_TABLES
    assert 'cache_state' not in IDENTITY_TABLES
    assert 'app_settings' not in IDENTITY_TABLES
    assert 'live_comp_global_stats' not in IDENTITY_TABLES
    assert 'live_comp_global_daily_stats' not in IDENTITY_TABLES
