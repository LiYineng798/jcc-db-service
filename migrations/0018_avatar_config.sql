-- Persist only bounded avatar parameters; keep existing avatar_color unchanged.
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_preset TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_expression TEXT;

UPDATE users
SET avatar_preset = (ARRAY['strobi', 'freddy', 'citrus', 'nova'])[1 + floor(random() * 4)::integer]
WHERE avatar_preset IS NULL;
UPDATE users
SET avatar_expression = (ARRAY['neutral', 'happy', 'wink', 'sleepy'])[1 + floor(random() * 4)::integer]
WHERE avatar_expression IS NULL;

ALTER TABLE users ALTER COLUMN avatar_preset SET DEFAULT 'strobi';
ALTER TABLE users ALTER COLUMN avatar_expression SET DEFAULT 'neutral';
ALTER TABLE users ALTER COLUMN avatar_preset SET NOT NULL;
ALTER TABLE users ALTER COLUMN avatar_expression SET NOT NULL;
ALTER TABLE users ADD CONSTRAINT users_avatar_preset_allowed
    CHECK (avatar_preset IN ('strobi','freddy','citrus','nova'));
ALTER TABLE users ADD CONSTRAINT users_avatar_expression_allowed
    CHECK (avatar_expression IN ('neutral','happy','wink','sleepy'));
