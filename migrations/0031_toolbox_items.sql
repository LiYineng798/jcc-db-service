-- Runtime overrides for public toolbox navigation and route lifecycle.
-- Built-in tool defaults live in the web service; rows here override visibility,
-- ordering, grouping, and display metadata without code deployments.
CREATE TABLE toolbox_items (
    tool_id TEXT PRIMARY KEY CHECK (length(trim(tool_id)) BETWEEN 1 AND 64),
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 80),
    description TEXT NOT NULL DEFAULT '',
    group_name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'visible' CHECK (status IN ('visible', 'unlisted', 'disabled')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    updated_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_toolbox_items_status_order
ON toolbox_items (status, sort_order, tool_id);
