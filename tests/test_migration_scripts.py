import sqlite3

import pytest

from scripts.migrate_sqlite_to_postgres import IDENTITY_TABLES, TABLE_ORDER, migrate_table


def test_table_order_loads_parent_tables_before_children():
    assert TABLE_ORDER.index('users') < TABLE_ORDER.index('lineups')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('likes')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('favorites')
    assert TABLE_ORDER.index('lineups') < TABLE_ORDER.index('reports')


def test_table_order_includes_current_tables():
    assert TABLE_ORDER == [
        'users',
        'automation_accounts',
        'lineups',
        'lineup_moderation',
        'lineup_moderation_events',
        'likes',
        'copy_events',
        'copy_action_events',
        'live_comp_copy_events',
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
        'search_events',
        'audit_logs',
        'rate_limits',
        'growth_events',
        'guestbook_messages',
        'feedback_threads',
        'feedback_events',
        'user_notifications',
        'notification_actors',
        'author_favorite_receipts',
        'orange_decks',
        'orange_deck_favorites',
        'orange_deck_likes',
        'patch_notes',
        'daily_admin_reports',
        'season_release_packages',
        'season_import_jobs',
        'season_active_releases',
        'season_release_events',
    ]


def test_identity_tables_exclude_text_primary_key_tables():
    assert 'users' in IDENTITY_TABLES
    assert 'lineups' in IDENTITY_TABLES
    assert 'cache_state' not in IDENTITY_TABLES
    assert 'app_settings' not in IDENTITY_TABLES
    assert 'live_comp_global_stats' not in IDENTITY_TABLES
    assert 'live_comp_global_daily_stats' not in IDENTITY_TABLES
    assert 'live_comp_copy_events' in IDENTITY_TABLES


@pytest.mark.parametrize('has_avatar_columns', [False, True])
def test_user_import_omits_missing_avatar_columns_to_use_target_defaults(has_avatar_columns):
    source = sqlite3.connect(':memory:')
    source.row_factory = sqlite3.Row
    target = sqlite3.connect(':memory:')
    target.row_factory = sqlite3.Row
    source.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, avatar_color TEXT)')
    source.execute("INSERT INTO users VALUES (7, '#abcdef')")
    if has_avatar_columns:
        source.execute('ALTER TABLE users ADD COLUMN avatar_preset TEXT')
        source.execute('ALTER TABLE users ADD COLUMN avatar_expression TEXT')
        source.execute("UPDATE users SET avatar_preset = 'nova', avatar_expression = 'wink'")
    target.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        avatar_color TEXT NOT NULL,
        avatar_preset TEXT NOT NULL DEFAULT 'strobi' CHECK (avatar_preset IN ('strobi','freddy','citrus','nova')),
        avatar_expression TEXT NOT NULL DEFAULT 'neutral' CHECK (avatar_expression IN ('neutral','happy','wink','sleepy'))
    )''')

    class Cursor:
        def __init__(self):
            self.insert_sql = None
            self.cursor = target.cursor()

        def execute(self, sql, params=()):
            if 'setval(' not in sql:
                return self.cursor.execute(sql, params)

        def fetchone(self):
            return self.cursor.fetchone()

        def executemany(self, sql, rows):
            self.insert_sql = sql
            return self.cursor.executemany(sql.replace('%s', '?'), rows)

    cursor = Cursor()
    assert migrate_table(source, cursor, 'users') == 1
    row = dict(target.execute('SELECT * FROM users').fetchone())
    assert row == {
        'id': 7, 'avatar_color': '#abcdef',
        'avatar_preset': 'nova' if has_avatar_columns else 'strobi',
        'avatar_expression': 'wink' if has_avatar_columns else 'neutral',
    }
    assert ('"avatar_preset"' in cursor.insert_sql) is has_avatar_columns
    assert ('"avatar_expression"' in cursor.insert_sql) is has_avatar_columns
    source.close()
    target.close()
