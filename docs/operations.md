# PostgreSQL 运维

通用跨服务更新流程见 [Web 运维](../../jcc-web-service/docs/operations.md)。
本文只维护可公开的结构、校验与恢复命令；真实拓扑、部署路径和恢复记录存放在私有运维系统，见 [仓库安全](repository-security.md)。

## 初次安装

本地用仓库 Compose；生产可安装系统 PostgreSQL，版本按环境选择。
同机部署监听 loopback；分离部署需同时配置可信网络、pg_hba 和防火墙，不开放公网 5432。

创建数据库与拥有 schema 权限的应用角色，凭据只存受限环境文件。
CLI 均显式要求 --database-url，不自动加载 .env。私有环境文件位置由 JCC_DB_ENV_FILE 显式指定。

以下变量由操作者在受控环境设置，不在公共仓库记录真实值：

```bash
: "${JCC_DB_DIR:?Set the DB repository directory}"
: "${JCC_DB_ENV_FILE:?Set an absolute private environment file path}"
cd "$JCC_DB_DIR"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
set -a
. "$JCC_DB_ENV_FILE"
set +a
.venv/bin/python scripts/apply_migrations.py --database-url "$JCC_DATABASE_URL"
.venv/bin/python scripts/verify_integrity.py --database-url "$JCC_DATABASE_URL"
```

迁移不创建生产管理员密码；新空库的管理员应通过受控账号初始化或经核对的 SQLite 导入准备。

## 结构变更

新 migration 按递增编号命名。apply_migrations 在事务中按文件名排序执行尚未记录的 SQL，
将文件 stem 写入 schema_migrations；失败不记成功。没有 down migration 或校验和机制，
已部署文件不能改写/改名，多个迁移进程不能并行执行。

```bash
psql "$JCC_DATABASE_URL" -c 'SELECT version, applied_at FROM schema_migrations ORDER BY version;'
```

- Web SQLite 的 db_schema/db_migrations 及专项 schema 必须同步。
- 新表检查 TABLE_ORDER 与 identity 恢复；完整性检查按实际引用增加，不能只做行数检查。
- 0015 的资料发布元数据依赖 Web uploads/releases；新增赛季本身不新增 DB 表。
- 0016 的审核状态与 lineups.status 联动；提案通过前不替换原内容，已读 revision 独立，
  处理事件保留。详细业务规则只在 [Web 审核文档](../../jcc-web-service/docs/lineup-moderation.md) 维护。

更新顺序：一致备份/停写 → DB 迁移及完整性 → Web/worker → 验收。
deploy/update.sh 只辅助拉取/迁移/检查，不做备份或服务停写；在脚本所属的仓库中执行，
运行前必须通过 JCC_DB_ENV_FILE 指定可读的绝对环境文件路径，文件内必须设置 JCC_DATABASE_URL。
缺少配置会在拉取、安装依赖或迁移前失败，不再使用固定生产路径。

## 备份与恢复

PostgreSQL dump 可获得 DB 一致快照；要让磁盘文件匹配，停写并停止 Web 与赛季 worker，
同时归档 instance、私有赛季资料、代码/静态基准和配置。命令在已加载环境后执行：

```bash
: "${BACKUP_DIR:?Set the private backup parent directory}"
umask 077
BACKUP_RUN="$(mktemp -d "$BACKUP_DIR/release-XXXXXXXX")"
pg_dump "$JCC_DATABASE_URL" -Fc -f "$BACKUP_RUN/database.dump"
pg_restore --list "$BACKUP_RUN/database.dump"
```

备份父目录须已存在且权限受限，每次创建新目录，不覆盖已有恢复点。检查内容/校验和并保存异机副本。
优先恢复到隔离空库验证；目标 URL 必须明确，先应用新目标所需角色/权限。
例如已准备目标连接串后：

```bash
pg_restore --dbname="$RESTORE_DATABASE_URL" --no-owner --no-acl --exit-on-error /path/to/verified.dump
.venv/bin/python scripts/verify_integrity.py --database-url "$RESTORE_DATABASE_URL"
```

这要求空目标，不能直接在有业务数据的库重放。
正式恢复前保存当前 DB/文件恢复点，停止两个 Web 进程服务，使用匹配的 DB/文件/代码并核验，
再启动服务与健康检查。恢复数据库不自动恢复图片；资料版本回滚优先走 Web 后台指针切换。

## SQLite 导入：适用范围与缺口

仅用于受控的旧库迁移，源库必须是已核验的完整 SQLite 快照，目标先应用所有迁移。
导入按 TABLE_ORDER 依赖顺序运行，源端缺表会跳过；批量插入后恢复数值 ID 序列。
--truncate-target 会清空目标名单并级联影响引用表，不能用于仍接受写入的数据库。

```bash
.venv/bin/python scripts/migrate_sqlite_to_postgres.py --sqlite-path /path/to/snapshot.sqlite3 --database-url "$TARGET_DATABASE_URL"
.venv/bin/python scripts/verify_counts.py --sqlite-path /path/to/snapshot.sqlite3 --database-url "$TARGET_DATABASE_URL"
.venv/bin/python scripts/verify_integrity.py --database-url "$TARGET_DATABASE_URL"
```

**已核对的限制**：现有 TABLE_ORDER 不包含 site_notices、live_comp_upload_jobs、password_reset_requests；
verify_counts 共用同一名单，全部通过也不能证明这些表已迁移。
旧 app_settings 的通知兼容数据不能代替完整的多通知库。上传任务/重置请求是否迁移还需确定保留政策。
改变导入名单前必须完成隔离数据迁移演练。完整备份/恢复使用 pg_dump/pg_restore。

## 验证边界

`python -m pytest -q` 验证脚本逻辑、SQL 文本及可移植约束，使用 SQLite/连接替身，
不是实际 PostgreSQL migration 测试。verify_integrity 也只是选定的业务检查，
不代表覆盖每个外键或完整 schema 差异。上线前应在真实隔离 PostgreSQL 验证迁移、导入和恢复。
