-- Daily admin reports: one snapshot row per report date.
-- Derived aggregate columns mirror the SQLite schema (db_schema.py) so the
-- same report columns are available from either database. payload_json holds
-- the full report. Additive only; no data changes to existing tables.

CREATE TABLE IF NOT EXISTS daily_admin_reports (
    report_date TEXT PRIMARY KEY,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    page_visits INTEGER NOT NULL DEFAULT 0,
    successful_copies INTEGER NOT NULL DEFAULT 0,
    payload_json TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_daily_admin_reports_generated_at
    ON daily_admin_reports (generated_at DESC);
