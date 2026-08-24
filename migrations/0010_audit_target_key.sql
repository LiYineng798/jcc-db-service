ALTER TABLE audit_logs
    ADD COLUMN IF NOT EXISTS target_key TEXT;

CREATE INDEX IF NOT EXISTS idx_audit_logs_target_key
    ON audit_logs (target_type, target_key, created_at DESC);
