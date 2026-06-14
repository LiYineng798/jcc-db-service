INSERT INTO cache_state (cache_key, revision, created_at, updated_at) VALUES
('home', 0, to_char(now(), 'YYYY-MM-DD HH24:MI:SS'), to_char(now(), 'YYYY-MM-DD HH24:MI:SS')),
('score', 0, to_char(now(), 'YYYY-MM-DD HH24:MI:SS'), to_char(now(), 'YYYY-MM-DD HH24:MI:SS'))
ON CONFLICT (cache_key) DO NOTHING;

INSERT INTO app_settings (setting_key, setting_value, updated_at) VALUES
('simulator_enabled', 'true', to_char(now(), 'YYYY-MM-DD HH24:MI:SS')),
('notice_enabled', 'false', to_char(now(), 'YYYY-MM-DD HH24:MI:SS')),
('notice_data', '{}', to_char(now(), 'YYYY-MM-DD HH24:MI:SS'))
ON CONFLICT (setting_key) DO NOTHING;

