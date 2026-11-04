-- Upgrade the deck library and independently scoped automation upload permission.
-- Existing decks remain readable until their authors supply a game plan code.
ALTER TABLE orange_decks ADD COLUMN plan_code TEXT NOT NULL DEFAULT '';
ALTER TABLE orange_decks ADD COLUMN season_id TEXT NOT NULL DEFAULT 'orange_s400001';
ALTER TABLE automation_accounts ADD COLUMN can_upload_decks INTEGER NOT NULL DEFAULT 0 CHECK (can_upload_decks IN (0, 1));
ALTER TABLE automation_accounts ADD COLUMN deck_seasons_json TEXT NOT NULL DEFAULT '[]';
