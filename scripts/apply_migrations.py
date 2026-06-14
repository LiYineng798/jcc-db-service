import argparse
from datetime import datetime
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / 'migrations'


def apply_migrations(database_url):
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                '''
            )
            for path in sorted(MIGRATIONS.glob('*.sql')):
                version = path.stem
                cursor.execute('SELECT 1 FROM schema_migrations WHERE version = %s', (version,))
                if cursor.fetchone():
                    continue
                cursor.execute(path.read_text(encoding='utf-8'))
                cursor.execute(
                    'INSERT INTO schema_migrations (version, applied_at) VALUES (%s, %s)',
                    (version, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                )
        connection.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database-url', required=True)
    args = parser.parse_args()
    apply_migrations(args.database_url)


if __name__ == '__main__':
    main()

