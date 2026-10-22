# 协作约定（人 + Codex + WorkBuddy 共用一个工作副本）

> 接手维护先读 `docs/HANDOVER.md`：进度盘点、代码地图、踩过的坑、已知缺陷与下一步路线图。

## 唯一工作副本

本目录（`photo-society`）是唯一在用的系统。`../cdu-photography-club` 是改版前的冻结副本，**不要在那里修改**。

前端 3000，后端 8000。只保留这一套进程，不要另起 3010/8010。

## 运行与数据

- 数据库：`backend/db.sqlite3`；上传文件：`backend/storage/`。两者不入库，**不要删除、重置或 flush**。
- 需要重置数据时，先把 `db.sqlite3` 和 `storage/` 备份到 `_backups/`，再操作。
- 本地启动：`scripts/start-local.ps1`；停止：`scripts/stop-local.ps1`。
- 示例内容用 `manage.py seed_demo`，必须带 `is_demo`；不得编造学校、人数、获奖、联系方式。

## 改前端

- 设计规范：`DESIGN.md`。样式只有 `frontend/src/app/globals.css` 一套，不要引入 Tailwind、CSS-in-JS 或第二套色板。
- 照片保留原始比例，不统一裁切；编号、图注、技术签条属于版式的一部分。
- 动效统一在 `frontend/src/app/motion.css` 与 `components/motion.tsx`；新增入场只加 `data-reveal`，不要引入第二套动效库。
- 不要用 JS 直接改 React 渲染节点的 class（会触发 hydration mismatch）；首屏标记与后续节点的处理方式见 `motion.tsx`。
- 改完执行：`cd frontend && npm run typecheck`，再 `next build` 确认。

## 改后端

- 业务规则只改 `backend/club/services.py` 与 `permissions.py`；不要在页面或后台另写一份。
- 模型改动必须 `makemigrations`，并补 `backend/club/tests/` 下的测试。
- 改完执行：`backend/manage.py test club.tests` 与 `makemigrations --check --dry-run`。

## 提交与回滚

- 提交前 `git status`，不要把 `db.sqlite3`、`storage/`、`.venv`、`node_modules`、`.next` 加进去。
- 回滚点：`git tag`（如 `backup/pre-contact-sheet-2026-10-19`）；合并前快照在 `../_backups/`。
- 大改前先开分支，不要直接改 `main`。

## 当前正式前端

- 首页 `/`，栏目 `/works`、`/activities`、`/about`，说明 `/privacy`。
- 所有页面使用 `frontend/src/app/(gallery)` 一套实现；不要恢复旧版、成员、档案、加入或期刊页面。
- `/field-journal` 只做旧链接跳转，不能再建平行站点。
- 以当前画廊样式、毛笔封面与会旗原字形为准，英文保留；历史 DESIGN 文档的六栏目规则已被后续用户要求替代。
- 历史数据库记录与原始上传文件留作后台资料；公开占位相册和旧资料已归档。
