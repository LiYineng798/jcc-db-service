# JCC Database Service

PostgreSQL schema、迁移、SQLite 导入和完整性检查工具；不运行 HTTP 服务。
业务页面/API 与数据库访问适配在 [Web 仓库](../jcc-web-service/README.md)。

## 本地启动

在本仓库执行（PowerShell，需要 Docker）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env 中 POSTGRES_PASSWORD，并同步下方连接串的密码。
docker compose up -d --wait
$env:JCC_DATABASE_URL='postgresql://jcc_app:replace-with-strong-password@127.0.0.1:5432/jcc'
python scripts/apply_migrations.py --database-url "$env:JCC_DATABASE_URL"
python scripts/verify_integrity.py --database-url "$env:JCC_DATABASE_URL"
```

Compose 自动读取 `.env`，Python CLI 不读取它，连接串须显式传入。
密码含 URL 保留字符时需编码。Docker 是本地开发方案；生产安装见 [运维](docs/operations.md)。

## 文件职责

| 目录/脚本 | 职责 |
| --- | --- |
| `migrations/` | 按编号递增的正式结构变更；应用情况存于 `schema_migrations` |
| `scripts/apply_migrations.py` | 在事务内应用尚未记录的迁移 |
| `scripts/migrate_sqlite_to_postgres.py` | 按外键依赖顺序导入，恢复 identity 序列 |
| `scripts/verify_counts.py` | 对照导入名单检查源/目标行数 |
| `scripts/verify_integrity.py` | 检查业务引用、审核状态与赛季发布指针 |
| `deploy/update.sh` | 拉取并迁移的辅助脚本；备份和停写由运维流程负责 |

## 验证

```powershell
python -m pytest -q
git diff --check
```

单元测试不要求真实 PostgreSQL；生产前仍须执行真实迁移和完整性检查。
**现有 SQLite 导入不是全库备份工具**，已知遗漏和恢复边界见 [运维](docs/operations.md)。

[AGENTS.md](AGENTS.md) 提供开发约束；生产拓扑与跨服务更新入口统一在 [Web 运维手册](../jcc-web-service/docs/operations.md)。
