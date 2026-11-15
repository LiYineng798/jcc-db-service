# 卡组投稿与统计数据契约

对应迁移：`0029_orange_deck_submissions`、`0030_orange_deck_analytics`。
字段类型、默认值、约束和索引以这两个 SQL 文件为准。本文说明 Web 接入时必须保持的业务语义。

## 交付边界

本次提供数据库结构、导入顺序、identity 恢复、完整性检查和 Web SQLite 镜像升级。
尚未实现投稿/处理 API、供稿署名展示、通知收件箱新类型、推荐算法、事件采集和报表聚合。
不要仅根据新表存在就启用功能或宣称已有采集数据。现有 Web 仍按旧方式提供卡组功能。

## 署名与权限

`orange_decks.user_id` 继续表示实际所有者；不能为了展示供稿人而改写它。
新增 `origin_type`、`provided_by_user_id`、`published_by_user_id`、`reviewed_card_version`、`reviewed_at`。

- 历史卡组为 `direct`，新增用户/复核字段为空；原代码、发布时间、复制计数和权限不变。
- 投稿建稿时，在同一 INSERT 中设 `origin_type='submission'` 和 `provided_by_user_id=submitter_user_id`。
  `user_id` 设为建稿管理员；`published_by_user_id` 在首次成功发布时记录执行管理员，后续修改不覆盖首次发布者。
- 公开署名使用供稿人；直接发布的旧卡组回退到所有者。供稿人不因此获得管理员草稿的编辑权限。
- 复核版本与时间必须同时为空或同时填写；`card_version` 保持原有资料快照意义，不能替代复核字段。
- 管理员只能通过专门受保护的处理入口跨用户编辑已关联投稿的卡组，不开放普通私有草稿。

## 投稿与处理历史

`orange_deck_submissions` 保存两种代码、赛季、提交者、处理管理员、结果卡组和状态。
标题可空，最多 24 字；备注 300 字；方案码 512 字；阵容码 20000 字；处理说明 1000 字。
代码不能为空。服务端仍须校验码格式/赛季、UUID、SHA-256 十六进制内容、JSON 和所有权限。
数据库长度检查不能代替这些校验。

`request_key` 是一次创建请求的 UUID，同一提交者重试复用；相同 key 不同内容应返回冲突。
`code_fingerprint` 是规范化 `[season_id, plan_payload, lineup_code]` 的 SHA-256。
建议固定使用 `json.dumps(value, ensure_ascii=False, separators=(',', ':'))` 后 UTF-8 编码。
`plan_payload` 去掉方案名称、按现有解析器校验并规范化编码载荷；阵容码沿用现有规范化器。
名称与备注不影响代码指纹。不要仅靠删除任意空白改写游戏载荷。

同一用户、赛季、指纹只能有一份处理中投稿（pending/processing/needs_info），不同用户可分别投稿。
跨用户重复需管理员判断，不能自动转移署名。`deck_id` 唯一，一份投稿最多复用一个完成用草稿。
关系只从投稿指向卡组，勿增设反向外键造成 SQLite 导入循环。

| 当前状态 | 允许的下一状态 |
| --- | --- |
| pending | processing / withdrawn |
| processing | pending / needs_info / published / rejected / duplicate |
| needs_info | pending / withdrawn |
| published / rejected / duplicate / withdrawn | 首版为终态，不自行重新打开 |

同状态修改、保存草稿和转派也递增 `version`。提交者只可修改 pending/needs_info；
processing 只能管理员处理。processing 必须有处理管理员；published 必须有结果卡组。
终态必须同时填写 `resolved_at`，其他状态必须为空。
duplicate 必须关联另一张同赛季、判定当时公开的卡组；其他状态的 `duplicate_of_deck_id` 为空。
后续卡组隐藏/软删除不改变投稿的历史采纳状态，也不使历史重复判断失效。

`orange_deck_submission_events` 每个投稿版本恰好一条，不物理删除。
创建事件为 `submit / from_status=NULL / to_status=pending / submission_version=1`。
每次更新以 `WHERE id=? AND version=?` 做乐观锁，成功后记录相同新版本事件。
`payload_json` 保存用户改动的必要快照；保存草稿事件记录卡组 ID/版本。仅提交者和管理员可读取。
action 枚举见迁移；同状态更新使用 update/save_draft/assign，退回用 request_info，补充后用 resubmit。

发布必须在一个事务中写卡组、投稿、事件、通知和审计；失败全部回滚。
现有 Web 部分保存 helper 会自行 commit，接入时必须拆出可组合写入层，不能连续调用并假设原子性。
在同一事务中先建草稿、再写 submission.deck_id；完整性检查在事务提交后执行。
退回/撤回/判重后的关联草稿继续保留为私有或软删除。

## 事件与统计口径

`orange_deck_activity_events` 记录实际成功的首次发布、隐藏、恢复、删除、资料复核、点赞和收藏变更。
操作与事件同事务写入。重复收藏请求不新增事件；恢复不是首次发布；编辑已发布内容不是新增发布。
当前点赞/收藏关系仍由原表维护，不能把关系行数与事件行数相加。

`copy_action_events` 新增 deck_id/code_type/actor_key/client_action_id/rank_eligible。
新卡组复制记录应使用：

```text
target_type = orange_deck
target_id = str(deck_id)
season_id = 卡组 season_id
code_type = plan 或 lineup
actor_key = 服务端确定的 user:<id> / visitor:<token> / ip:<address>
client_action_id = 每次实际复制手势的 UUID，网络重试复用
rank_eligible = 服务端判断的 0/1，默认 0
```

actor_key 不能信任客户端；管理员、自动化账号、卡组所有者和供稿人的自复制不加热门权重。
同一动作 ID 只存一次，重复 ID 与原目标/代码类型/行为者不一致时拒绝。旧客户端缺 action ID 可兼容 NULL。
不要使用 INSERT OR IGNORE 吞掉未知 CHECK/外键错误；明确捕获幂等冲突。
普通阵容/实时榜单旧记录保留空新字段及 rank_eligible=0，不会进入卡组热门统计。

`orange_deck_copies` 保留五分钟有效复制去重：两种代码共享 `(deck_id,copy_key,bucket_start)`。
共享计分与两种代码的动作事件同事务写入。行为者复制两种代码可有 2 次成功动作，但同桶仅 1 次有效复制；
推荐再按卡组/行为者/日去重，最多 1 份信号。动作数、有效复制数、独立人数必须分别命名。
旧有效复制行继续计入历史总量，不能补造代码类型或事件时间。

`orange_deck_visit_events` 是每日去重访问，surface 为 library/detail。
library 不填 deck_id；detail 必填。分别以日期/访问者、日期/访问者/卡组去重。
不记录预取、管理员、机器人或数据请求；只有实际展示卡组库标签/公开详情时采集。
这不是 PV 或曝光表；不得用它声称有准确卡片 CTR，也不重复增加首页 PV。

首次正式采集事件时，在同一事务内幂等写 app_settings 的 `deck_analytics_started_at`。
迁移不写这个值，防止部署 schema 到启用采集之间的数据空窗被当作零。
所有采集渠道应一起启用；如果分批上线，应分别增加对应起点，报表标注覆盖范围。
时间文本沿用站点 `now_text()` 与业务时区，不混用 UTC 字符串；日期桶使用相同日期口径。

日报继续使用 `daily_admin_reports.payload_json`，建议 `payload_version=2`，卡组字段以 `deck_` 前缀区分。
历史缺键显示“未采集”，采集起始日显示部分时段，不重建整段历史或重置已有总数。
热门算法在 Web 使用近期有效复制/收藏/点赞、时间衰减和冷启动补位；本次未固定权重或增加预计算排行表。

## 通知接入

新增 `kind='deck_submission'`，关联 `deck_submission_id`；此时 lineup_id/feedback_id 都必须为空。
group_key 使用 `deck_submission:<id>`，接收人必须等于提交者；复用 revision/read_count/notice_state。
不要把提交者自身重复保存都变成新通知；管理员接单、退回、采纳、拒绝/判重按产品定义通知。
先完成 Web 收件箱 SQL、分类、序列化、类型和私有详情路由，再开始创建这种通知；
当前 Web 通知 UI 尚不认识新 kind。notification_actors 保持只用于旧互动消息。

## 部署与验证

按照 [运维](operations.md) 先备份/停写，在隔离 PostgreSQL 验证迁移与导入，再迁移 DB 后部署 Web。
0029/0030 不删除/改写旧业务行，也不建立生产管理员。已应用迁移不可改名/改写。
Web 启动只检查所需表/列，不代替 PostgreSQL 迁移。SQLite 的升级在 bootstrap 写入前独立事务执行，
通知表重建保留 ID、自增高水位、索引、触发器和 notification_actors；失败回滚并恢复外键开关。

导入顺序已将卡组放在投稿之前，投稿放在通知之前，卡组放在 copy_action_events 之前。
新增四张表均纳入 TABLE_ORDER、identity 恢复和计数；verify_counts 复用 TABLE_ORDER。
完整性检查覆盖供稿归属、赛季、历史事件连续性、通知接收人和事件引用，不替代 API 权限校验。
既有导入工具仍不是全库备份工具，遗漏边界见 [运维](operations.md#sqlite-导入适用范围与缺口)。
