-- Independent optional game lineup code; old decks retain their plan codes.
ALTER TABLE orange_decks ADD COLUMN lineup_code TEXT NOT NULL DEFAULT '';
