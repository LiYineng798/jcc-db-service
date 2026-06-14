import argparse
import sys

import psycopg


CHECKS = [
    (
        'lineups.user_id -> users.id',
        '''
        SELECT COUNT(*)
        FROM lineups l
        LEFT JOIN users u ON u.id = l.user_id
        WHERE u.id IS NULL
        ''',
    ),
    (
        'likes.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM likes child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'copy_events.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM copy_events child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'favorites.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM favorites child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'reports.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM reports child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'reports.reporter_user_id -> users.id',
        '''
        SELECT COUNT(*)
        FROM reports child
        LEFT JOIN users parent ON parent.id = child.reporter_user_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'recent_lineup_views.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM recent_lineup_views child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'recent_lineup_copies.lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM recent_lineup_copies child
        LEFT JOIN lineups parent ON parent.id = child.lineup_id
        WHERE parent.id IS NULL
        ''',
    ),
    (
        'growth_events.ref_lineup_id -> lineups.id',
        '''
        SELECT COUNT(*)
        FROM growth_events child
        LEFT JOIN lineups parent ON parent.id = child.ref_lineup_id
        WHERE child.ref_lineup_id IS NOT NULL AND parent.id IS NULL
        ''',
    ),
]


def verify_integrity(database_url):
    failures = []
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for label, sql in CHECKS:
                cursor.execute(sql)
                count = int(cursor.fetchone()[0] or 0)
                print(f'{label}: {count}')
                if count:
                    failures.append((label, count))
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database-url', required=True)
    args = parser.parse_args()
    failures = verify_integrity(args.database_url)
    if failures:
        print('Integrity verification failed', file=sys.stderr)
        return 1
    print('Integrity verification passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

