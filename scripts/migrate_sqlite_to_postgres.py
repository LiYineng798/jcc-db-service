import argparse
import sqlite3

import psycopg


TABLE_ORDER = [
    'users',
    'lineups',
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
    'audit_logs',
    'rate_limits',
    'growth_events',
    'guestbook_messages',
    'patch_notes',
    'daily_admin_reports',
]

IDENTITY_TABLES = {
    'users',
    'lineups',
    'likes',
    'copy_events',
    'copy_action_events',
    'live_comp_copy_events',
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
}


def sqlite_columns(sqlite_connection, table):
    rows = sqlite_connection.execute(f'PRAGMA table_info({table})').fetchall()
    return [row['name'] for row in rows]


def table_exists(sqlite_connection, table):
    row = sqlite_connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return bool(row)


def quote_ident(name):
    return '"' + name.replace('"', '""') + '"'


def truncate_target(cursor):
    tables = ', '.join(quote_ident(table) for table in reversed(TABLE_ORDER))
    cursor.execute(f'TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE')


def reset_identity(cursor, table):
    cursor.execute(f'SELECT COALESCE(MAX(id), 0) FROM {quote_ident(table)}')
    max_id = int(cursor.fetchone()[0] or 0)
    if max_id <= 0:
        return
    cursor.execute(
        'SELECT setval(pg_get_serial_sequence(%s, %s), %s, true)',
        (table, 'id', max_id),
    )


def migrate_table(sqlite_connection, pg_cursor, table):
    if not table_exists(sqlite_connection, table):
        return 0
    columns = sqlite_columns(sqlite_connection, table)
    if not columns:
        return 0
    order_sql = ' ORDER BY id' if 'id' in columns else ''
    rows = sqlite_connection.execute(f'SELECT * FROM {table}{order_sql}').fetchall()
    if not rows:
        return 0
    quoted_columns = ', '.join(quote_ident(column) for column in columns)
    placeholders = ', '.join('%s' for _ in columns)
    sql = f'INSERT INTO {quote_ident(table)} ({quoted_columns}) VALUES ({placeholders})'
    pg_cursor.executemany(sql, [tuple(row[column] for column in columns) for row in rows])
    if table in IDENTITY_TABLES:
        reset_identity(pg_cursor, table)
    return len(rows)


def migrate(sqlite_path, database_url, truncate=False):
    sqlite_connection = sqlite3.connect(sqlite_path)
    sqlite_connection.row_factory = sqlite3.Row
    try:
        with psycopg.connect(database_url) as pg_connection:
            with pg_connection.cursor() as pg_cursor:
                if truncate:
                    truncate_target(pg_cursor)
                counts = {}
                for table in TABLE_ORDER:
                    counts[table] = migrate_table(sqlite_connection, pg_cursor, table)
            pg_connection.commit()
            return counts
    finally:
        sqlite_connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite-path', required=True)
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--truncate-target', action='store_true')
    args = parser.parse_args()
    counts = migrate(args.sqlite_path, args.database_url, truncate=args.truncate_target)
    for table, count in counts.items():
        print(f'{table}: {count}')


if __name__ == '__main__':
    main()

