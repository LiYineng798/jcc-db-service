ALTER TABLE guestbook_messages
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'unread';

ALTER TABLE guestbook_messages
    ADD COLUMN IF NOT EXISTS read_at TEXT;

ALTER TABLE guestbook_messages
    ADD COLUMN IF NOT EXISTS read_by BIGINT REFERENCES users(id);

ALTER TABLE guestbook_messages
    ADD COLUMN IF NOT EXISTS archived_at TEXT;

ALTER TABLE guestbook_messages
    ADD COLUMN IF NOT EXISTS archived_by BIGINT REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_guestbook_messages_status_created_at
ON guestbook_messages (status, created_at DESC);
