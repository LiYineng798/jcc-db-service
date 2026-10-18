import argparse
import sys

import psycopg


CHECKS = [
    ('active season release matches season and is ready', '''
        SELECT COUNT(*) FROM season_active_releases a
        LEFT JOIN season_release_packages p ON p.id=a.release_id
        WHERE a.release_id IS NOT NULL AND (p.id IS NULL OR p.season_id<>a.season_id OR p.state<>'ready' OR p.published_at IS NULL)
    '''),
    ('previous season release matches season and was published', '''
        SELECT COUNT(*) FROM season_active_releases a
        LEFT JOIN season_release_packages p ON p.id=a.previous_release_id
        WHERE a.previous_release_id IS NOT NULL AND (p.id IS NULL OR p.season_id<>a.season_id OR p.published_at IS NULL)
    '''),
    ('every season release has an import job', '''
        SELECT COUNT(*) FROM season_release_packages p
        LEFT JOIN season_import_jobs j ON j.release_id=p.id WHERE j.id IS NULL
    '''),
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
    ('moderation restriction matches lineup status', '''
        SELECT COUNT(*) FROM lineups l LEFT JOIN lineup_moderation m ON m.lineup_id=l.id
        WHERE (l.status='banned' AND (m.lineup_id IS NULL OR m.state NOT IN ('banned','pending','rejected')))
           OR (m.state IN ('banned','pending','rejected') AND l.status<>'banned')
    '''),
    ('moderation events reference existing lineups and actors', '''
        SELECT COUNT(*) FROM lineup_moderation_events e
        LEFT JOIN lineups l ON l.id=e.lineup_id LEFT JOIN users u ON u.id=e.actor_user_id
        WHERE l.id IS NULL OR u.id IS NULL
    '''),
    ('search_events.user_id -> users.id', '''
        SELECT COUNT(*) FROM search_events e LEFT JOIN users u ON u.id=e.user_id
        WHERE e.user_id IS NOT NULL AND u.id IS NULL
    '''),
    ('report feedback belongs to reporter', "SELECT COUNT(*) FROM feedback_threads f LEFT JOIN reports r ON r.id=f.source_id WHERE f.source_type='report' AND (r.id IS NULL OR r.reporter_user_id<>f.user_id OR r.lineup_id<>f.lineup_id)"),
    ('guestbook feedback belongs to sender', "SELECT COUNT(*) FROM feedback_threads f LEFT JOIN guestbook_messages m ON m.id=f.source_id WHERE f.source_type='guestbook' AND (m.id IS NULL OR m.user_id IS NULL OR m.user_id<>f.user_id)"),
    ('feedback owner exists', 'SELECT COUNT(*) FROM feedback_threads f LEFT JOIN users u ON u.id=f.user_id WHERE f.user_id IS NOT NULL AND u.id IS NULL'),
    ('feedback events reference thread', 'SELECT COUNT(*) FROM feedback_events e LEFT JOIN feedback_threads f ON f.id=e.thread_id WHERE f.id IS NULL'),
    ('notification owner exists', 'SELECT COUNT(*) FROM user_notifications n LEFT JOIN users u ON u.id=n.user_id WHERE u.id IS NULL'),
    ('feedback notification belongs to submitter', "SELECT COUNT(*) FROM user_notifications n LEFT JOIN feedback_threads f ON f.id=n.feedback_id WHERE n.kind='feedback' AND (f.id IS NULL OR f.user_id IS NULL OR f.user_id<>n.user_id)"),
    ('author notification belongs to author', "SELECT COUNT(*) FROM user_notifications n LEFT JOIN lineups l ON l.id=n.lineup_id WHERE n.kind IN ('like','favorite','copy') AND (l.id IS NULL OR l.user_id<>n.user_id)"),
    ('notification read count is bounded', 'SELECT COUNT(*) FROM user_notifications WHERE read_count>event_count'),
    ('favorite receipts reference users and lineups', 'SELECT COUNT(*) FROM author_favorite_receipts r LEFT JOIN users u ON u.id=r.user_id LEFT JOIN lineups l ON l.id=r.lineup_id WHERE u.id IS NULL OR l.id IS NULL'),

    ('notification actors reference interaction notices and users', "SELECT COUNT(*) FROM notification_actors a LEFT JOIN user_notifications n ON n.id=a.notification_id LEFT JOIN users u ON u.id=a.actor_user_id WHERE n.id IS NULL OR u.id IS NULL OR n.kind NOT IN ('like','favorite','copy') OR n.user_id=a.actor_user_id"),

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

