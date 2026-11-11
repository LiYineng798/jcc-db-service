-- Admin reports split Orange Fortune deck copies (target_type 'orange_deck') by the copied code.
-- NULL for lineup / live-comp copies and for history recorded before this migration.
ALTER TABLE copy_action_events ADD COLUMN IF NOT EXISTS code_type TEXT;

-- Hot deck ranking reads only a recent window of effective copies.
CREATE INDEX IF NOT EXISTS idx_orange_deck_copies_bucket
    ON orange_deck_copies (bucket_start, deck_id, copy_key);
