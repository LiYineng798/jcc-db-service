-- Fixed striped-sphere avatar; only a six-digit ink color is stored.
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_color TEXT;
UPDATE users
SET avatar_color = (ARRAY['#0021ed', '#059669', '#7c3aed', '#ea580c', '#e11d48', '#334155', '#0284c7', '#4f46e5'])[1 + floor(random() * 8)::integer]
WHERE avatar_color IS NULL;
ALTER TABLE users ALTER COLUMN avatar_color SET DEFAULT '#0021ed';
ALTER TABLE users ALTER COLUMN avatar_color SET NOT NULL;
ALTER TABLE users ADD CONSTRAINT users_avatar_color_hex CHECK (avatar_color ~ '^#[0-9a-fA-F]{6}$');
