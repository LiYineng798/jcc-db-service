-- Public participant avatars for author notifications. Never store anonymous identifiers.
CREATE TABLE IF NOT EXISTS notification_actors (
    notification_id BIGINT NOT NULL REFERENCES user_notifications(id) ON DELETE CASCADE,
    actor_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (notification_id, actor_user_id)
);
