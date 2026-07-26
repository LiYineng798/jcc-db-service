-- Daily copy leaderboard: filter copy_action_events by created_at range.
-- Additive only; no data changes.

CREATE INDEX IF NOT EXISTS idx_copy_action_events_created_at
    ON copy_action_events (created_at);
