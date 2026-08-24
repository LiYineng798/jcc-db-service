CREATE TABLE IF NOT EXISTS live_comp_upload_jobs (
    id TEXT PRIMARY KEY,
    season_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'preview',
    stage TEXT NOT NULL DEFAULT 'validated',
    filename TEXT NOT NULL DEFAULT '',
    input_path TEXT NOT NULL,
    total_bytes INTEGER NOT NULL DEFAULT 0,
    uploaded_bytes INTEGER NOT NULL DEFAULT 0,
    item_total INTEGER NOT NULL DEFAULT 0,
    item_done INTEGER NOT NULL DEFAULT 0,
    image_total INTEGER NOT NULL DEFAULT 0,
    image_done INTEGER NOT NULL DEFAULT 0,
    current_item TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    result_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT NOT NULL DEFAULT '',
    created_by INTEGER,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_live_comp_upload_jobs_status_created_at
    ON live_comp_upload_jobs (status, created_at);

CREATE INDEX IF NOT EXISTS idx_live_comp_upload_jobs_created_by_created_at
    ON live_comp_upload_jobs (created_by, created_at DESC);
