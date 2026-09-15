# DB 开发约定

本仓库只负责 PostgreSQL schema、SQLite 导入、完整性检查与数据库运维。
Flask/API/前端以及 SQLite 适配属于相邻 Web 仓库。

- 启动、验证和文档入口见 [README](README.md)，实际操作见 [运维](docs/operations.md)。
- 新结构增加递增编号的 SQL migration；已应用迁移不能改名或改写。迁移按文件名顺序执行并记录在 `schema_migrations`。
- 同步 Web 的 `db_schema.py`、`db_migrations.py` 及专项 schema 模块；跨服务变更分别提交，先迁移 DB，再部署 Web。
- 新表同时检查导入的 `TABLE_ORDER`、identity 恢复和完整性查询。源端缺表可跳过不等于完整迁移。
- 赛季发布表只存元数据；恢复须包含 Web 持久文件。阵容审核状态必须与 `lineups.status` 一致，不能让旧 Web 绕过封禁。
- 不提交数据库、dump、凭据、日志或环境文件，不清理其他 worktree 和交付资料。
- 结构/工具变更补充聚焦测试，运行 `python -m pytest -q` 和 `git diff --check`。本地测试主要使用 SQLite 可移植 SQL及连接替身，不能替代真实 PostgreSQL 迁移与恢复演练。
- README/AGENTS 只保留长期入口和约束；不重复列出每张表、每次部署和验收结果。部署前核实现况，不从历史记录推断已上线版本。
