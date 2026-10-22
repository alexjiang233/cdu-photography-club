# 验收记录

日期：2026-10-19，Asia/Shanghai。

## 已实际执行

| 验证 | 结果 |
| --- | --- |
| Django 系统检查与迁移一致性 | 通过 |
| 正式设置 `check --deploy` | 通过，无警告；确认正式后台为 OTPAdminSite |
| PostgreSQL 17.11 后端测试 | 28 项全部通过，无跳过 |
| SQLite 本地流程 | 早期 20 项中 19 项通过，并发测试按设计跳过；正式数据库已另行全量验证 |
| Next.js TypeScript 检查 | 通过 |
| Next.js 生产构建 | 通过，公开页面、成员页与 robots 路由均构建成功 |
| 部署 YAML 解析 | 通过；仅 HTTPS 网关暴露公网端口 |
| 本地 HTTP 健康、首页、作品、活动、资料、关于、登录、隐私、robots、后台与图片/会话接口 | 200 |
| 浏览器真实登录与投稿 | 登录、保存草稿、选文件上传、图片处理、修改说明、提交审核、退出成功 |
| 浏览器手机导航与主题筛选 | 导航可展开；筛选后的主题和 URL 一致；无水平溢出 |
| 图片加载 | 已检查首页无损坏图片 |
| SQLite 备份 | 20 个文件校验通过，数据库完整性检查通过 |
| PostgreSQL 备份恢复 | 35 个文件校验通过；恢复至独立库，核对 6 个作品系列、1 个资料版本及 7 个原文件校验值 |

## 安全与业务覆盖

测试覆盖：作品提交/审核/发布/撤回；空作品拒绝提交；发布后锁定；非法内容编号；原片与展示图权限；内部资料不进入公开搜索；文件伪装拒绝上传；元数据去除；跨成员文件引用拒绝；本人上传文件找回；活动重复报名/满员/取消/重新报名；两连接同时竞争最后名额；报名联系方式保护；讨论审核；登录 CSRF；后台上传复用校验；管理员 TOTP 与重放拒绝；管理员会话缺少 OTP 时拒绝访问 API；成员不可自提权；文件版本顺序与下载；创建时不可绕过审核设置发布状态。

## 视觉与交互检查

主要依据 frontend-design、Emil design engineering 与 Vercel Web Interface Guidelines。已修复的事项：

| Before | After | Why |
| --- | --- | --- |
| 前后端尾斜杠规则不同，图片重定向循环 | 明确保留 API 尾斜杠，图片链接带内容版本 | 图片与会话请求正常到达后端 |
| 窄手机标题被压成四行 | 480px 以下标题与说明分层布局 | 主标题保留清楚的两行结构 |
| 草稿关联活动只能选择最近一页 | 搜索活动并保留当前选项 | 往期记录同样可关联 |
| 上传中断后只能重新上传 | 本人已上传图片列表可重新关联 | 避免重复文件与额度消耗 |
| 作品页的活动筛选没有传递 | 列表与分页保留活动条件 | 活动关联浏览保持一致 |

保留照片比例的大图查看支持 Escape 关闭、左右方向键切换和焦点管理。控件有标签与 focus，异步反馈可播报，主要按钮可触控；尊重 reduced-motion，无自动轮播或滚动劫持。

## 不能视为已验证的部分

- 未实际启动 Docker Compose 整套容器；未验证公网 DNS、TLS 签发、云网络和真实域名。
- 当前本地图片任务同步执行；生产 Redis/Celery 多进程、ClamAV 病毒库、S3 和真实 SMTP 尚未接入验收。
- 当前仅有监控接入点、容器健康与日志，没有配置外部告警接收人。
- 已做桌面和 390px 手机浏览器检查，未覆盖所有实体手机及浏览器组合。
- 示例内容不代表协会真实作品、成员或活动。临时 UI 验证账号将在交付前禁用。

完整流程与迁移/备份恢复说明见 OPERATIONS.md；架构与权限不变量见 ARCHITECTURE.md。

## 2026-10-19 印样版改版

改版范围：公开界面整体替换（首页、作品、活动、成员、档案、加入），新增作品档案编号与公开招新报名；业务状态机与权限未改。

| 验证 | 结果 |
| --- | --- |
| `manage.py check` | 通过，无 issue |
| `makemigrations --check --dry-run` | 无待生成迁移 |
| `manage.py test club.tests` | 28 项，27 通过、1 项并发测试按设计跳过 |
| `npm run typecheck` | 通过 |
| `next build --webpack` | 通过；路由含 `/`、`/works`、`/events`、`/members`、`/archive`、`/join`、`/search`、`/login`、`/privacy`、`/dashboard` 等 |
| 公开路由状态 | `/`、`/works`、`/events`、`/members`、`/archive`、`/join`、`/login`、`/privacy`、`/search` 均 200 |
| `/about` | 308 → `/members`（`next.config.ts` permanent redirect） |
| 招新接口 | 空姓名返回 400；合法提交返回 201 并写库；后台「入会申请」可见 |
| 浏览器表单 | 填写并提交 `/join` 成功，显示"已收到"提示 |
| 登录与成员中心 | 使用本地预览账号登录成功；`/dashboard`、`/dashboard/submit`、个人设置渲染正常 |
| 响应式 | 390 / 768 / 1024 三档，全部页面无横向溢出 |
| 图片比例 | 竖幅 2:3 作品在 4:3 外框内完整显示（letterbox），未裁剪 |
| 截图 | `qa/home-desktop.jpg`、`qa/home-mobile.jpg` 已替换为新版 |

说明：

- 本地预览用 `next dev --webpack`（本机依赖以 junction 复用，Turbopack 不接受工作区外的 `node_modules`）。生产容器内依赖是本地安装，不受影响。
- `next start` 不适用于 `output: 'standalone'`；正式部署仍按 `deploy/` 的 Nginx + standalone 方式，`/api/` 由 Nginx 直接转给 Django，不经过 Next rewrites。
- 本轮未启动 Docker Compose，未验证公网域名、TLS、SMTP、ClamAV；管理员 TOTP 仅沿用原有测试覆盖。

补充：空站状态

临时把全部示例作品/活动/档案归档后检查首页：首屏显示"第一组作品，正在征集"的征集面板，四个统计为 `00`，作品与活动区块给出具体投稿指引，档案显示"待归档"，没有空白破图或重叠。截图见 `qa/empty-home-desktop.jpg`、`qa/empty-home-mobile.jpg`。检查后已恢复示例内容。


## 2026-10-19 动效层

| 验证 | 结果 |
| --- | --- |
| 首屏水合 | 无 hydration mismatch（首屏标记延迟到 `requestIdleCallback`，后续节点由 MutationObserver 接管） |
| 滚动入场 | 首页 22 个 `data-reveal`，首屏 6 个直接显示，滚动后增至 17 个 |
| 客户端导航 | 首页 → 作品：6 个印样全部入场，页面淡入完成 |
| 手机菜单 | 打开后焦点在"首页"，`body` 滚动锁定；Esc 关闭并恢复滚动 |
| 阅读进度 | 作品详情滚动 1200px 时进度条宽度 91.6% |
| 复制链接 | 点击后按钮变"已复制"，底部 toast 显示 |
| 年份高亮 | 档案页滚动后对应年份链接获得 `.active` |
| 减少动效 | `prefers-reduced-motion: reduce` 下隐藏元素数为 0 |
| 控制台 | 无错误 |
