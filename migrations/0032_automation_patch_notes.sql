ALTER TABLE automation_accounts ADD COLUMN patch_note_access TEXT NOT NULL DEFAULT 'none'
    CHECK (patch_note_access IN ('none', 'draft', 'publish'));
