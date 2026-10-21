-- Replace dedicated API tokens with normal password/session accounts.
ALTER TABLE automation_accounts ADD COLUMN can_touch INTEGER NOT NULL DEFAULT 0 CHECK (can_touch IN (0, 1));
ALTER TABLE automation_accounts ADD COLUMN touch_seasons_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE automation_accounts ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1;
DROP TABLE IF EXISTS automation_imports;
ALTER TABLE automation_accounts DROP COLUMN token_hash;
ALTER TABLE automation_accounts DROP COLUMN token_prefix;
