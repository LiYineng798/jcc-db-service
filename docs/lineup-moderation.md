# 0016 阵容封禁与修改重审

迁移 `0016_lineup_moderation.sql` 必须在对应 Web 版本上线前应用。新增两张表：

- `lineup_moderation`：每个阵容当前的封禁/待审/退回/通过/解除状态、原因、封禁前展示状态、用户提交版本、审核说明和用户通知已读状态。
- `lineup_moderation_events`：按顺序保留操作者、动作、原因、提交前后快照和时间。软删除阵容不会删除记录。

原有 `lineups.status` 使用 `banned` 表示整个限制期间，`version` 执行条件更新并防止旧页面覆盖审核；原始阵容字段只在审核通过时替换。封禁前为 hidden 的阵容恢复后继续隐藏。用户通知仅保留 unread/read，已移除归档状态。通知状态有独立 `revision`，不会改变审核版本。

SQLite 导入顺序为 users → lineups → lineup_moderation → lineup_moderation_events，事件表恢复 identity 序列；旧 SQLite 没有新表时跳过对应导入。计数校验沿用共享 TABLE_ORDER。完整性检查增加封禁状态一致性及事件的作者/阵容引用检查。

本地验证运行 `python -m pytest -q`。新测试执行迁移中的可移植 SQL（把 PostgreSQL identity 改成 SQLite identity），校验状态约束、提交版本完整性、引用、导入和完整性检查。尚未连接真实 PostgreSQL 执行本迁移。

部署顺序：先备份 → DB `scripts/apply_migrations.py` → Web → `scripts/verify_integrity.py` 与 Web 健康及审核链路冒烟。无新增生产配置、无 worker。回滚需要停止写入并恢复匹配的 Web/DB 版本；不要只回滚 Web，使旧通用编辑入口可再次修改封禁记录。界面和 API 合约见 Web 的 `docs/lineup-moderation.md`。
