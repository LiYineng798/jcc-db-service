import argparse
import sqlite3
import sys

import psycopg

from migrate_sqlite_to_postgres import TABLE_ORDER, table_exists


def sqlite_count(connection, table):
    if not table_exists(connection, table):
        return 0
    return connection.execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']


def postgres_count(cursor, table):
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    return cursor.fetchone()[0]


def verify_counts(sqlite_path, database_url):
    sqlite_connection = sqlite3.connect(sqlite_path)
    sqlite_connection.row_factory = sqlite3.Row
    mismatches = []
    try:
        with psycopg.connect(database_url) as pg_connection:
            with pg_connection.cursor() as cursor:
                for table in TABLE_ORDER:
                    left = sqlite_count(sqlite_connection, table)
                    right = postgres_count(cursor, table)
                    print(f'{table}: sqlite={left} postgres={right}')
                    if left != right:
                        mismatches.append((table, left, right))
    finally:
        sqlite_connection.close()
    return mismatches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite-path', required=True)
    parser.add_argument('--database-url', required=True)
    args = parser.parse_args()
    mismatches = verify_counts(args.sqlite_path, args.database_url)
    if mismatches:
        print('Count verification failed', file=sys.stderr)
        return 1
    print('Count verification passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

