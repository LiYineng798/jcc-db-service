-- Expand available shapes without changing any user's saved avatar.
ALTER TABLE users DROP CONSTRAINT users_avatar_preset_allowed;
ALTER TABLE users ADD CONSTRAINT users_avatar_preset_allowed
    CHECK (avatar_preset IN ('strobi','freddy','citrus','nova','sunee','cloudee','sprout','bloom'));
