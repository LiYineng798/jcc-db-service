-- Expand saved expressions without changing any user's current avatar.
ALTER TABLE users DROP CONSTRAINT users_avatar_expression_allowed;
ALTER TABLE users ADD CONSTRAINT users_avatar_expression_allowed
    CHECK (avatar_expression IN ('neutral','happy','wink','sleepy','curious','surprised','shy','determined'));
