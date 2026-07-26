-- Performance-audit indexes (additive only; no data changes).
-- Mirrors jcc-web-service db_schema.EXTRA_INDEX_STATEMENTS additions.

-- Homepage list: filter by season + status, order by updated_at DESC, id DESC.
CREATE INDEX IF NOT EXISTS idx_lineups_season_status_updated_id
    ON lineups (season_id, status, updated_at DESC, id DESC);

-- New/returning visitor split probes prior visits per visitor.
CREATE INDEX IF NOT EXISTS idx_visit_events_visitor_date
    ON visit_events (visitor_key, visit_date);

-- Admin overview "today" counters.
CREATE INDEX IF NOT EXISTS idx_login_events_created_at
    ON login_events (created_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs (created_at);

CREATE INDEX IF NOT EXISTS idx_reports_status
    ON reports (status);

CREATE INDEX IF NOT EXISTS idx_users_created_at
    ON users (created_at);

-- Account history lists: filter by user, order by updated_at DESC, id DESC.
CREATE INDEX IF NOT EXISTS idx_recent_lineup_views_user_updated
    ON recent_lineup_views (user_id, updated_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_recent_lineup_copies_user_updated
    ON recent_lineup_copies (user_id, updated_at DESC, id DESC);
