-- Daily admin reports probe visit/copy events by client IP (top visitor-IP
-- panel and the per-IP returning/copied flags). Additive indexes only.

CREATE INDEX IF NOT EXISTS idx_visit_events_ip_date
    ON visit_events (ip_address, visit_date);

CREATE INDEX IF NOT EXISTS idx_copy_action_events_ip_created_at
    ON copy_action_events (ip_address, created_at);
