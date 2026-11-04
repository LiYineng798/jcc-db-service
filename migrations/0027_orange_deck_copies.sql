-- Effective plan-code copies are independent of ordinary lineup statistics.
-- One account / guest IP per deck per five-minute window; no historical backfill.
CREATE TABLE IF NOT EXISTS orange_deck_copies (
    deck_id BIGINT NOT NULL REFERENCES orange_decks(id),
    copy_key TEXT NOT NULL,
    bucket_start TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (deck_id, copy_key, bucket_start)
);
