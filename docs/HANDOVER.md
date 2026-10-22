> **2026-10-22 正式站点已替换旧版**：直接访问 `/`。仅保留照片、活动、关于、隐私；源码在 `frontend/src/app/(gallery)`。旧页面与多套样式已删除，`/field-journal` 仅兼容跳转。清理详情见 [CANONICAL_SITE.md](CANONICAL_SITE.md)。以下为历史交接记录，不代表当前前端结构。

# 摄影协会网站 · 移交文档

> 最新变更：前台登录、成员中心与投稿入口撤下，留言向全部访客开放并继续审核；管理后台暂时保留。以下历史盘点中的成员操作描述不代表当前前台入口，当前规则见 [PUBLIC_ACCESS.md](PUBLIC_ACCESS.md)。

> 交接时间：2026-10-19 22:50
> 交接对象：Codex（已通过 MCP 接入）与下一任维护者
> 工作副本：`C:\Users\JiangKaiyang\Documents\ChatGPT\软件移植\photo-society`
> 当前提交：`f91a0d3`（main，工作区干净）

---

## 0. 三十秒速览

| 项 | 内容 |
| --- | --- |
| 这是什么 | 成都大学摄影协会官网。公开站 + 成员投稿 + 审核发布 + 档案归档 + 招新报名 |
| 技术栈 | Next.js 16（App Router）+ React 19；Django 5.2 + DRF；SQLite（本地）/ Postgres（生产）；Celery + Redis（生产） |
| 规模 | 前端 16 个页面、后端 13 个模块、8 个容器、28 项后端测试 |
| 设计语言 | 「印样」（contact sheet）：纸白 `#F7F5F0` / 墨 `#171613` / 暗房红 `#B33A2B`，无衬线 + 等宽标签 |
| 当前状态 | **功能完整、可演示、可上线**；缺真实素材，未部署公网 |
| 本地端口 | 前端 3000 / 后端 8000（**不要另起 3010/8010**） |
| 一句话判断 | 工程底子能扛真实使用；产品内核建议走「活动照片交付」，门面走「当期展览」 |

---

## 1. 接手第一步

### 1.1 按这个顺序读

1. `AGENTS.md` —— 硬性协作约定（唯一副本、端口、数据安全、视觉红线）。**先读这个，违反它会直接搞坏数据或进程。**
2. 本文 —— 全貌、坑、路线图。
3. `DESIGN.md` —— 视觉与动效规范。
4. `docs/ARCHITECTURE.md` —— 实体关系、权限模型、核心不变量。
5. `docs/PRODUCT_REVIEW.md` —— 产品判断与改版记录。
6. 需要细节时再查 `docs/REVIEW-2026-10-19.md`（2 万字全面评估）、`docs/API.md`、`docs/OPERATIONS.md`、`docs/MOTION.md`、`docs/VERIFICATION.md`、`docs/LAUNCH_WITHOUT_ASSETS.md`。

### 1.2 跑起来

```powershell
cd C:\Users\JiangKaiyang\Documents\ChatGPT\软件移植\photo-society
.\scripts\start-local.ps1          # 起 8000 + 3000
.\scripts\stop-local.ps1           # 停
```

脚本会先检查端口占用，被占用会直接抛错——这是有意的，避免两套实例抢同一份 SQLite。

手动启动（等价）：

```bash
cd backend && ../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload
cd frontend && npm run dev            # 3000
```

`frontend/next.config.ts` 已把 `/api`、`/admin`、`/static` 反代到 `http://127.0.0.1:8000`，前端只开一个口就够。

### 1.3 三条「别做」

- **别在 `../cdu-photography-club` 改代码**。那是改版前的冻结副本，只保留历史和回滚价值（已加 `ARCHIVED.md`）。
- **别删 `backend/db.sqlite3` 或 `backend/storage/`**，也别 `flush`。里面是真实排过版的内容。
- **别把 `db.sqlite3`、`storage/`、`.venv`、`node_modules`、`.next` 提交进 git**。

> 注：本次会话结束时 3000/8000 可能已被回收（`Get-NetTCPConnection` 查不到监听）。跑一次 `start-local.ps1` 即可恢复，不影响数据。

---

## 2. 现在到哪一步了

### 2.1 已完成并验证

| # | 事项 | 落点 | 验证 |
| --- | --- | --- | --- |
| 1 | 一级栏目收敛为六个：首页 / 作品 / 活动 / 成员 / 档案 / 加入 | `frontend/src/components/header.tsx` | 全路由 200 |
| 2 | `/about` 永久重定向到 `/members`，原「关于」页拆除 | `frontend/next.config.ts` | 308 |
| 3 | 首页改为「协会当前状态」：收录统计、本期印样、近期活动、成员、年度档案、招新 | `frontend/src/app/page.tsx` | 统计来自 `/api/site/` 实时计算 |
| 4 | 作品年度档案编号（`2026-001`…`2026-006`），发布时自动分配 | `backend/club/services.py:assign_code` | 7 组中 6 组已编号 |
| 5 | 照片保留原始比例，统一外框内 letterbox，不裁切 | `globals.css` `.frame .box img` | 竖幅 2:3 实测完整显示 |
| 6 | 活动分「即将开始 / 往期」，默认近期优先 | `api/public.py` + `models.py` | 修正了原先「最远一场排第一」 |
| 7 | 档案按年份索引 + 分类筛选，允许「待归档」 | `frontend/src/app/archive/page.tsx` | 年份滚动高亮实测 |
| 8 | 公开招新报名：`/join` → `/api/join/` → 后台「入会申请」 | `components/join-form.tsx`、`api/public.py:JoinApplicationView` | 浏览器提交成功；空姓名 400；限速 6 次/小时 |
| 9 | 反机器人：隐藏字段 `website`，填了返回 201 但不入库 | 同上 | 已测 |
| 10 | 21 项动效与交互层 | `app/motion.css`、`components/motion.tsx`、`app/template.tsx` | 清单见 `docs/MOTION.md` |
| 11 | 手机菜单：遮罩、Esc、焦点陷阱、滚动锁 | `components/header.tsx` | 实测 |
| 12 | 空站状态（0 作品 / 0 成员 / 待归档） | `page.tsx`、`globals.css` | 临时归档示例内容实测，截图在 `qa/empty-home-*.jpg` |
| 13 | 图片灯箱：缩放淡入、手机左右滑、键盘方向键 | `components/gallery.tsx` | 实测 |
| 14 | 作品/活动/档案详情「复制链接」 | `components/motion.tsx:CopyLink` | 含剪贴板不可用时的回退 |
| 15 | 两套副本合并为唯一工作副本 | 本目录 | 数据保留，迁移 0003–0005 已应用 |
| 16 | CI：后端 Postgres 测试 + 前端 typecheck/build | `.github/workflows/checks.yml` | 已启用 |
| 17 | 文档 9 份 + 验收截图 6 张 | `docs/`、`qa/` | — |

### 2.2 明确没做（不是遗漏，是排期）

- 真实素材（Logo、有人脸的活动照、成员自述、招新时间/群号）
- 活动照片的批量交付（找自己 + 打包下载）
- 作者反馈回路（浏览量、评论通知）
- 已发布资料的「追加版本」流程
- HEIC 上传、客户端压缩
- OG 分享卡、sitemap、结构化数据、`next/image` 的 srcset
- Django 后台的前台化（现在活动/成员/档案仍靠原生 admin）
- 公网部署（`deploy/` 与 `compose.yml` 已就绪，未实跑）
- E2E 测试（只有后端单测 + 手工浏览器验收）

---

## 3. 代码地图

### 3.1 前端（`frontend/src`）

| 路径 | 作用 | 注意 |
| --- | --- | --- |
| `app/layout.tsx` | 根布局、站点信息、页头页脚、`MotionRoot` | `site/` 接口失败时有兜底，不要去掉 |
| `app/template.tsx` | 每次路由变化重挂载，负责页面淡入 | 与 `motion.tsx` 配合 |
| `app/page.tsx` | 首页（六个区块） | 统计数字全部来自接口，不写死 |
| `app/works/page.tsx` | 作品印样墙 + 筛选 | `WorkCard` 传 `index` 做错峰 |
| `app/works/[id]/page.tsx` | 作品详情：大图、图注、技术签条、同活动其他照片 | 参数表是单列 baseline 布局 |
| `app/events/page.tsx`、`events/[id]` | 活动列表（upcoming/past）与详情（名额、报名状态） | 状态由 `eventState()` 统一计算 |
| `app/members/page.tsx`、`members/[id]` | 成员网格（2 列）与个人档案 | 空位显示「等待本人填写」 |
| `app/archive/page.tsx`、`archive/[id]` | 年份索引 + 分类筛选；文档详情与版本 | `data-spy-*` 驱动年份高亮 |
| `app/join/page.tsx` | 招新说明 + 表单 + FAQ | 表单在 `components/join-form.tsx` |
| `app/search/page.tsx` | 三类内容聚合搜索 | 只搜标题/简介/标签，不搜 PDF 正文 |
| `app/dashboard/*` | 成员中心、投稿编辑器、账号设置 | `editor-shell` 已居中 |
| `app/login`、`reset-password`、`privacy` | 登录、改密、隐私说明 | — |
| `app/globals.css` | **唯一**样式文件（印样系统） | 不要引入 Tailwind / CSS-in-JS |
| `app/motion.css` | 动效与交互样式 | 与 `globals.css` 分开维护 |
| `components/motion.tsx` | `MotionRoot`（入场、页头、进度、回顶）、`CopyLink` | **JS 改 class 的时序问题见 §7.4** |
| `components/ui.tsx` | `WorkCard`、`EventRow`、`DocumentRow`、`DemoBadge`、`eventState` | 列表入场标记在这里 |
| `components/gallery.tsx` | 原生 `<dialog>` 灯箱 | 触摸滑动 + 键盘 |
| `components/header.tsx` | 页头、桌面导航、手机菜单 | 焦点陷阱逻辑在此 |
| `lib/server-api.ts` / `client-api.ts` | 服务端/客户端取数 | 服务端带 `no-store` |
| `lib/types.ts` | 接口类型 | `Collection.code` 已加 |

### 3.2 后端（`backend`）

| 路径 | 作用 | 注意 |
| --- | --- | --- |
| `club/models.py` | 12 个实体：Profile / Tag / Asset / Event / Collection / Photo / Registration / Document / DocumentVersion / Comment / Notice / AuditLog / JoinApplication / SiteSettings | `Event.Meta.ordering = -starts_at`，前端用 `when=` 覆盖 |
| `club/services.py` | **唯一业务规则**：`transition()` 状态机、`register()` 名额锁、`assign_code()` 编号、`audit()` | 页面/API/admin 都走这里，不要另写一份 |
| `club/permissions.py` | 对象级权限、可见性过滤 | 不要在序列化层再判一次 |
| `club/serializers.py` | 序列化；`RegistrationSerializer` 不含联系方式 | — |
| `club/api/content.py` | 作品/活动/资料/评论的 ViewSet | 审核动作在 `EditorialViewSet` |
| `club/api/public.py` | 站点信息、成员、统计、招新、健康检查 | `stats` 只统计已发布+公开 |
| `club/api/files.py` | 上传、资源变体（原片 / 展示图 / 缩略图） | 原片只给本人或资料管理员 |
| `club/uploads.py` | 校验、EXIF 处理、缩略图 | 白名单不含 HEIC |
| `club/tasks.py` | Celery：图片处理、病毒扫描 | 本地不跑 worker，走同步兜底 |
| `club/admin.py` | 原生后台 + 审核动作 | 「入会申请」已注册 |
| `club/migrations/0003–0005` | 招新表、编号字段、编号回填 | 部署前必须 `migrate` |
| `config/settings.py` | 配置；匿名限速 300/min、登录 10/min | — |

### 3.3 其他

| 路径 | 作用 |
| --- | --- |
| `design/prototype/` | 静态可点原型（`python build.py` 生成 7 页），保留作设计基准 |
| `design/README.md` | 结构决策与「没抄 rmultra 的三件事」 |
| `docs/` | 9 份文档，见 §13 |
| `qa/` | 验收截图：首页桌面/手机、空站桌面/手机、动效菜单、历史预览 |
| `scripts/` | `start-local.ps1`、`stop-local.ps1`、`fetch-demo-assets.py`、`verify-backup.py` |
| `deploy/` | Nginx、Caddy、standalone 启动、CI 模板 |
| `compose.yml` | 8 服务：caddy / proxy / frontend / backend / worker / antivirus-updater / db / redis |

---

## 4. 信息架构与关键决策

### 4.1 为什么是这六个栏目

首页 / 作品 / 活动 / 成员 / 档案 / 加入。

- **不设「关于」页**：旧版的「关于」塞了协会介绍 + 成员墙 + 招新说明 + FAQ，是四合一，也是「套娃」的起点。现在介绍进首页，人进成员页，联系方式进加入页。`/about` 用 308 挡掉旧链接。
- **不设「留言墙」**：Discussion 挂在作品/活动下面，空着的东西不占一级入口。
- **不设「站点导航」**：参照对象 `rmultra.cn` 的 `/sites` 是「导航的导航」，纯套娃，明确不抄。
- **档案是一等栏目**：旧版资料库有版本、权限、审计，是被低估的资产，升级为主栏目而不是砍掉。

### 4.2 产品定位（还没最终拍板，但方向清楚）

三条候选：

- **A 当期展览驱动**：首页即当前展览，视觉冲击强，但一年只有几次高潮。
- **B 活动照片交付工具**：活动结束后，参与者能按作者找自己、能打包下载。**这是「网站消失会变难」的事。**
- **C 校园影像档案**：按年份沉淀，长期价值高，但短期没人看。

**建议：B 做内核，A 做门面，C 让 B 自然长出来。** 现在代码是 A 的壳 + B 的骨架（作品可关联活动、有报名、有权限），但 B 的关键动作（批量交付）还没做。

### 4.3 「可核对」原则

站上每一个数字都必须能从库里算出来：6 组作品、6 张照片、3 场活动、1 份档案。**不要写「成员 200+、获奖 50 项」**——那是模板感的来源，也是谎。

---

## 5. 设计系统（改之前必须知道）

### 5.1 Token

```
纸白 --paper   #F7F5F0      墨 --ink      #171613
次色 --ink-2   #5F5B52      线 --line     #DAD4C7
暗房红 --red   #B33A2B
```

- 字体：无衬线正文（系统栈）+ 等宽做标签/编号。**禁宋体大标题**（旧版问题：跨设备三种相貌）。
- 圆角只给控件（按钮 2px），图片是自然矩形。
- **禁**：军旅金绿配色、卡片阴影、渐变蒙层、装饰性大数字。

### 5.2 印样规则

- 每格有编号（`2026-006`）、白边、图注条。
- 照片保原始比例，外框统一，**裁剪权归作者**。
- 红笔圈选只用于「本期选片」，且是一张，不是每张。

### 5.3 动效规则

- 时长：按下 120ms / 悬停 180ms / 状态 260ms / 入场 560ms；错峰 45ms，最多 6 项。
- 曲线：进入 `cubic-bezier(.22,1,.36,1)`；只动 `transform` 与 `opacity`。
- 无滚动劫持、无自动轮播、无无限装饰动画。
- `prefers-reduced-motion: reduce` 下全部关闭，内容直接可见。
- 新增入场只加 `data-reveal`（需要错峰加 `style={{ '--i': n }}`），**不要引入第二套动效库**。

---

## 6. 数据与账号

### 6.1 当前数据

| 表 | 数量 | 说明 |
| --- | --- | --- |
| `club_collection` | 7 | 6 组已发布（`2026-001`…`2026-006`），1 组归档（无编号，归档时不分配） |
| `club_event` | 3 | 示例活动，均 `is_demo` |
| `club_document` | 1 | 示例档案 |
| `club_profile` | 2 | 示例成员档案 |
| `club_joinapplication` | 0 | 测试数据已清理 |
| `auth_user` | 2 | `demo-content`、`local-qa-review`，**均非 superuser** |

### 6.2 后台账号

**现在没有可用的管理员账号。** 需要时自建：

```bash
cd backend
../.venv/Scripts/python.exe manage.py createsuperuser
```

后台地址：`http://127.0.0.1:3000/admin/`（经 Next 反代）或 `http://127.0.0.1:8000/admin/`。

角色用 `manage.py bootstrap_roles` 初始化（`scripts/start-local.ps1` 已包含）。

### 6.3 示例内容

`manage.py seed_demo` 可重建示例内容，全部带 `is_demo=True`，前端会显示「示例」标记。图片是 Unsplash 风景建筑，**没有人脸**——这是「模板感」的一半原因。

> 注意：`seed_demo` 会写入内容，不要在已有真实内容的库上盲跑；先看命令实现。

---

## 7. 踩过的坑（重点，按类别）

### 7.1 环境与进程

**① 两套副本、两套进程，数据分叉**
- 症状：改的页面在 3010 看到，3000 却是旧版；接口统计两边不一样。
- 原因：`cdu-photography-club` 与 `photo-society` 各跑一套，各有一份 SQLite。
- 解法：合并到 `photo-society`，`cdu-photography-club` 加 `ARCHIVED.md` 冻结；`AGENTS.md` 写死「唯一工作副本 + 只开 3000/8000」。
- 预防：任何「再起一个端口对比一下」的念头都要掐掉；要对比用 git 分支。

**② 端口被占用，启动脚本直接抛错**
- 症状：`端口 8000 已被占用`。
- 原因：旧进程没退（Windows 上 `runserver --noreload` 经常留孤儿）。
- 解法：`.\scripts\stop-local.ps1`；顽固时按端口找 PID 杀掉。
- 预防：启动前先查 `Get-NetTCPConnection -LocalPort 3000,8000`。

**③ 自建 venv / node_modules 浪费 600MB**
- 症状：在新副本里 `pip install` 卡十分钟，`npm ci` 又装 422MB。
- 原因：副本原本没有依赖目录，而隔壁已经有一份。
- 解法：删掉自建的，用 junction 复用；最终合并成一个目录后不再需要。
- 教训：**先看同级目录有没有现成环境，再决定装不装。**

**④ pip 默认源超时**
- 症状：`pip install` 十分钟无输出，临时目录堆了几个 `pip-*`。
- 解法：`-i https://pypi.tuna.tsinghua.edu.cn/simple --only-binary=:all: --no-cache-dir`。
- 预防：国内网络直接上镜像，别硬等。

**⑤ Turbopack 不接受工作区外的 `node_modules`**
- 症状：junction 方案下 `next dev` 报找不到模块 / 解析失败。
- 解法：本机预览用 `next dev --webpack`，构建用 `next build --webpack`。
- 现状：合并后依赖是本地安装，**Turbopack 已可正常 `npm run build`**，这条只在复用外部依赖时成立。

**⑥ `.next` 残留导致 500 或静态资源 404**
- 症状：页面 500，或图片全部 404，但后端直连正常。
- 原因：上一次构建/开发中断，`.next` 里有半成品；也可能 dev 与 build 产物混用。
- 解法：停进程 → 删 `frontend/.next` → 重启。
- 预防：切换 dev/build、切分支后先清缓存。

**⑦ `next start` 与 `output: 'standalone'` 不兼容**
- 症状：`next start` 报错或找不到 `.next/BUILD_ID`。
- 原因：`next.config.ts` 是 `output: 'standalone'`，产物要走 `node .next/standalone/server.js`。
- 解法：本地用 `npm run dev`；生产按 `deploy/` 的 standalone 方式（Nginx 静态 + Node 服务）。
- 预防：不要用 `next start` 验证本项目。

**⑧ CI 模板没启用**
- 症状：README 说「自动检查未启用」，但 `.github/workflows/checks.yml` 存在。
- 原因：历史遗留（上传 token 无 `workflow` 权限）。
- 现状：workflow 已提交并生效；`deploy/github-actions-checks.yml` 保留为同内容模板。

### 7.2 Git

**⑨ `dubious ownership`**
- 症状：`git status` 报 `detected dubious ownership`。
- 原因：目录属主是 `CodexSandboxOffline`，当前 Windows 用户不是它。
- 解法：`git config --global --add safe.directory "C:/Users/.../photo-society"`（已加）。
- 预防：换机器 / 换目录后要重加。

**⑩ 把数据提交进 git**
- 症状：`git status` 里出现 `db.sqlite3`、`storage/`、`.next`、`.venv`。
- 原因：`cp -r` 或脚本生成了新目录，而 `.gitignore` 覆盖不到。
- 解法：检查 `.gitignore`；已跟踪的用 `git rm --cached`。
- 预防：提交前必看 `git status`（`AGENTS.md` 已写）。

### 7.3 后端

**⑪ 活动排序反了**
- 症状：首页「近期活动」显示 11-09、11-02、10-26——最远的一场排第一。
- 原因：`Event.Meta.ordering = ['-starts_at']`，对「报名」场景正好是反的。
- 解法：API 支持 `when=upcoming|past`，默认未开始优先且升序；模型排序保留给后台。
- 预防：**模型默认排序不等于业务默认排序**，列表接口要显式声明。

**⑫ 已发布资料的「版本」加不进去**
- 症状：要改一版，必须撤稿 → 草稿 → 公开页消失 → 加版本 → 再审核。
- 原因：`transition()` 的状态机不允许 `published` 直接追加版本。
- 现状：**这是产品缺陷，未修**。建议见 §9（P2-1）。
- 预防：状态机改动要连带补测试，别只改一处。

**⑬ 招新表单的隐藏字段**
- 症状：机器人提交也返回 201，但库里没有。
- 原因：`website` 字段有值就短路返回，故意不给爬虫反馈。
- 注意：这不是 bug，改的时候别「修」掉。

**⑭ 匿名限速打满**
- 症状：开发时反复刷新后接口 429。
- 原因：原来 `anon: 120/min`，页面一次加载多个请求。
- 解法：调到 `300/min`。
- 预防：生产按真实流量再评，别直接照搬。

**⑮ 迁移与代码不同步**
- 症状：`no such column: club_collection.code`。
- 原因：拉了新代码没 `migrate`。
- 解法：`manage.py migrate`；部署时迁移必须先于新容器。
- 预防：CI 已加 `makemigrations --check --dry-run`。

### 7.4 前端

**⑯ hydration mismatch（最值得记的一条）**
- 症状：开发环境左下角 `1 Issue`，控制台报 `Hydration failed because the server rendered HTML didn't match the client`。
- 原因：`motion.tsx` 在 React 水合**之前**就给服务端渲染的节点加了 class（`js-motion`、`is-in`），DOM 与 React 的预期不一致。
- 解法（现行）：
  1. 首屏元素先标记 `is-in`，再打开 `js-motion` 隐藏规则，避免闪一下；
  2. 初始化延后到 `requestIdleCallback`（带 3s 兜底）；
  3. 后续导航产生的新节点交给 `MutationObserver` 扫描，而不是重新挂载整套逻辑。
- 预防：**任何「JS 直接改 React 渲染节点 class」的写法都会踩这条**。要做装饰性 class，加在 `documentElement`/`body`，或等水合后。

**⑰ 照片被 CSS 裁掉**
- 症状：竖幅照片在 4:3 卡里被切成横的，构图被破坏。
- 原因：`.frame .box` 固定 `aspect-ratio` + `object-fit: cover`。
- 解法：外框固定，图片 `position:absolute; inset:0; width/height:100%; object-fit: contain`，竖图左右留衬底。
- 预防：**裁剪权归作者**是硬规则，别再写 `cover`。

**⑱ 空状态盖住按钮**
- 症状：手机端「提交作品 / 加入我们」被压到面板外，点不到。
- 原因：`.hero-empty` 用了 `position:absolute; inset:0`，父级高度由 `aspect-ratio` 决定，内容超出被裁。
- 解法：改成常规流式块，`min-height: clamp(300px, 32vw, 370px)`。
- 预防：空状态要按「内容可能比设计稿长」来写布局。

**⑲ 类名冲突**
- 症状：页头品牌小方块跑到页面左上角。
- 原因：新加的红圈 SVG 用了 `.mark`，而品牌方块也叫 `.mark`，被同一条 `position:absolute` 规则命中。
- 解法：品牌改成 `.brand-mark`。
- 预防：新增全局 class 前 `grep` 一遍。

**⑳ 网格空列 / 边框错位**
- 症状：成员页右侧多一列空白，或边框双线。
- 原因：`gap: 1px` + 背景色画线，空元素撑出了格子。
- 解法：改成 `gap: 0` + 每格 `border-right/bottom`，容器只留 `border-top/left`。
- 预防：用边框画网格比用背景色稳。

**㉑ 手机端图注/时间挤成一行**
- 症状：`周五 · 18:40` 在 390px 下换行错位；图注作者名贴到标题。
- 解法：`.strip` 改 `display:block`；活动时间的 `.time` 在手机隐藏；图注作者加 `.who` 单独成行。
- 预防：图注条这类「两段文字 + 分隔」的结构，手机必须显式改布局。

**㉒ 筛选栏第一个元素被推右**
- 症状：作品页搜索框前多出一大段空白。
- 原因：`.filter-search { margin-left: auto }` 命中了第一个元素。
- 解法：`.filters > .filter-search:first-child { margin-left: 0 }`。
- 预防：`auto` 边距要配 `:first-child` 兜底。

**㉓ 删除页面后旧链接 404**
- 症状：`/about` 直接 404。
- 原因：页面文件删了，链接还在页脚/外部收藏里。
- 解法：`next.config.ts` 加 `redirects()`，308 到 `/members`。
- 预防：**下线页面前先搜全站引用**，并加重定向。

**㉔ 剪贴板 API 不可用**
- 症状：点「复制链接」没反应或弹 `prompt`。
- 原因：非 HTTPS / 无权限时 `navigator.clipboard` 抛错。
- 解法：回退到 `textarea + execCommand('copy')`，再不行也不弹 prompt（至少给 toast 反馈）。
- 预防：涉及浏览器能力的交互都要有降级路径。

**㉕ 后端直连正常、经 Next 反代 404**
- 症状：`/api/assets/{id}/thumbnail/` 在 8000 是 200，在 3000 是 404。
- 原因：rewrite 规则末尾斜杠与请求路径不匹配（`skipTrailingSlashRedirect: true` 下更容易撞）。
- 解法：规则写成 `/api/:path*/` → `${backend}/api/:path*/`，请求统一带尾斜杠。
- 预防：改 rewrite 后用 curl 分别打后端和代理，不要只看页面。

---

## 8. 已知缺陷与风险（诚实清单）

| # | 问题 | 影响 | 落点 | 优先级 |
| --- | --- | --- | --- | --- |
| 1 | 没有真实素材，示例图全是 Unsplash 风景、无一张人脸 | 观感仍像模板；「示例」标记满天飞 | 内容，不是代码 | **P0** |
| 2 | 活动照片无法批量交付；原片只有本人/资料管理员能下 | 参与者拿不到自己出镜的照片——社团最高频的麻烦 | `api/files.py`、`Photo` 模型 | **P1** |
| 3 | 作者零反馈：无浏览量，评论不写 `Notice` | 投稿没回报，第二年没人投 | `api/content.py` 评论分支 | **P1** |
| 4 | 已发布资料不能追加版本 | 改一版要撤稿重审，公开页会消失 | `services.transition()` | P2 |
| 5 | 不支持 HEIC | iPhone 默认格式，新生第一次投稿就失败 | `uploads.py:34` | P2 |
| 6 | 无 OG/Twitter 卡片、无 sitemap、无结构化数据 | 分享到微信/QQ 没有缩略图，搜索引擎收录差 | `app/layout.tsx` 的 metadata | P1 |
| 7 | 全站 0 处 `next/image` | 没有 srcset，手机下大图浪费流量 | 各页面 `<img>` | P2 |
| 8 | 成员/活动/档案管理仍靠 Django 原生后台 | 社长不会用；「内部使用」这半句没兑现 | 需要后台前台化 | P1 |
| 9 | 无邮件通知（报名、审核、评论） | 所有通知靠人肉 | `tasks.py` | P2 |
| 10 | 本地不跑 Celery/Redis，图片处理走同步 | 批量上传会卡请求 | `tasks.py`、`compose.yml` | P2 |
| 11 | 只有后端单测，无 E2E | 前端交互靠手工验收，回归成本高 | `frontend/` 无测试目录 | P2 |
| 12 | SQLite 单文件 | 并发写入有限；多实例会锁 | `settings.py` | 上线前切 Postgres |
| 13 | 无自动化备份 | 现在只有手工 `_backups/` 快照 | `scripts/verify-backup.py` 未接定时 | P1 |
| 14 | 部署链路未实跑 | Nginx/Caddy/TLS/SMTP/ClamAV 均未验证 | `deploy/`、`compose.yml` | 上线前 |

---

## 9. 下一步路线图

### P0 · 让它像真的（1 周内可完成）

1. **素材落地**：按 §10 清单要三样东西；先用自己拍的 3 张校园照片开第一组，署自己的名。
2. **撤掉示例标记**：真实内容发布后归档所有 `is_demo` 内容，`site.has_demo` 自动转 false。
3. **补 OG 卡片**：`app/layout.tsx` 的 `metadata` 加 `openGraph`/`twitter`，用第一张作品做 `opengraph-image`；补 `app/sitemap.ts`。
4. **备份定时化**：`scripts/verify-backup.py` 接 Windows 计划任务，每天导出 `db.sqlite3` + `storage/` 到 `_backups/`。

验收：`curl /api/site/` 的 `has_demo` 为 false；分享链接有缩略图；`_backups/` 有当日文件。

### P1 · 把「内核」做出来

**P1-1 活动照片交付（最该做）**

- 现状：`Photo` 只挂 `Collection`，`Collection.event` 可关联活动，所以「某场活动的照片」已经能查（`/api/collections/?event=`）。
- 要加：
  - `GET /api/events/{id}/photos/`：按作者分组返回，带缩略图；权限＝该活动报名者或协会成员。
  - `GET /api/events/{id}/download/`：流式 zip（`zipfile` + `StreamingHttpResponse`），只打展示图不打原片；文件名带作者与编号。
  - 前端活动详情加「本场照片 / 打包下载 / 按作者看」三个入口。
- 验收：报名者登录后能下载到自己出镜那组；非报名者 403；100 张照片 zip 不爆内存（流式）。

**P1-2 作者反馈回路**

- `Photo` 或 `Collection` 加浏览计数（用 `F()` 自增，避免竞态），详情页 `useEffect` 上报一次（同 session 去重）。
- 评论创建后写 `Notice` 给作者（`content.py` 评论分支），成员中心显示未读数。
- 验收：投一稿、发一条评论，作者账号在 `/dashboard` 看到通知。

**P1-3 后台前台化（最小版）**

- 只做三件事：活动增删改、成员档案编辑、档案上传。
- 复用现有 `EditorialViewSet` 与 `transition()`，不要另写业务规则。
- 验收：社长不登录 Django admin 也能发一场活动。

### P2 · 打磨

- 已发布资料追加版本：`transition()` 加 `revise` 动作，`DocumentVersion` 直接追加，公开页不消失。
- HEIC：`uploads.py` 白名单加 `image/heic`，用 `pillow-heif` 转 JPEG 后再走现有流程。
- `next/image` 改造：先做作品详情与列表，`sizes` 按印样栅格写。
- 邮件通知：Celery 任务 + 模板，先做「报名成功」「审核结果」两种。
- E2E：Playwright 跑 5 条主路径（首页→作品→灯箱、加入→提交、登录→投稿、活动报名、档案下载）。

### 如果只有一天

做 P0-1（素材）+ P0-3（OG 卡）+ P1-1 的第一半（按作者看照片）。这三件对「像真的」和「有用」的边际收益最高。

---

## 10. 素材清单与要资源的原话

### 10.1 需要什么（按重要性）

| 项 | 数量 | 用途 | 没有时怎么办 |
| --- | --- | --- | --- |
| 协会全称 + 成立时间 | 1 条 | 页脚、首页引言 | 用「成都大学摄影协会」，成立时间留空 |
| Logo | 1 个（SVG/PNG 透明） | 页头、favicon、OG | 用文字标 + 现有 `icon.svg` |
| 有人脸的活动照 | 8–12 张 | 首页、活动详情、成员页 | 先用自己拍的，宁可少不要风景图库 |
| 成员一句话 | 3 条 | 成员页 | 显示「等待本人填写」，不编 |
| 最近一次活动：日期/地点/人数 | 1 条 | 活动页 | 只写已知字段，不猜 |
| 招新时间、QQ 群、邮箱 | 各 1 | 加入页 | 表单照收，回复方式写「活动日现场」 |
| 旧海报 / 队服 / 器材柜照片 | 3–5 张 | 档案、静物 | 拍静物不用求人 |

### 10.2 找社长的话（可直接复制）

> 我在做协会官网，结构已经搭好了，现在卡在三样东西上。不需要你写文案：
> ① 协会全称和成立时间；
> ② 上一届活动清单，截图也行；
> ③ 有没有用过的 Logo、海报或队服照片。
> 没有 Logo 我先用文字标。给我这三样，我这周能上线一个能用的版本。

把「我没素材」换成「我需要这三样才能上线」——前者是诉苦，后者是资源申请。

### 10.3 拿到素材后怎么进系统

1. 登录 → `/dashboard/submit` → 建作品 → 上传 → 写图注 → 关联活动 → 提交审核。
2. 管理员在 `/admin/` 用审核动作发布；发布时自动分配 `YYYY-NNN` 编号。
3. 作品想上首页：勾 `featured`。
4. 成员档案：`/admin/club/profile/` 填写，`display_name` 与账号分开（毕业撤权后署名仍在）。

---

## 11. 运行、部署与回滚

### 11.1 本地

```powershell
.\scripts\start-local.ps1              # dev
.\scripts\start-local.ps1 -Production  # 构建后跑
.\scripts\stop-local.ps1
```

日志在 `.local-run/frontend.log`、`.local-run/backend.log`，PID 在 `.local-run/processes.json`。

### 11.2 生产

见 `docs/OPERATIONS.md`。要点：

- `compose.yml` 八服务；Caddy 负责 TLS，Nginx 负责静态与反代。
- 前端 `output: 'standalone'`，不走 `next start`。
- `/api`、`/admin`、`/static` 由 Nginx 直接转 Django，**不经过 Next rewrites**。
- 迁移先于新容器：`docker compose run --rm backend python manage.py migrate`。
- 必须配 `.env`（参考 `.env.example`）：`SECRET_KEY`、`ALLOWED_HOSTS`、Postgres、S3（可选）、SMTP、ClamAV。

### 11.3 回滚

```bash
# 整体回到改版前
git reset --hard backup/pre-contact-sheet-2026-10-19

# 回到某次提交
git reset --hard 2d2b3b8

# 源码快照
../_backups/photo-society_pre-merge_2026-10-19.tar.gz
../_backups/cdu-photography-club_2026-10-19_pre-redesign.tar.gz
```

**回滚代码前先备份 `db.sqlite3` 与 `storage/`**：迁移 0004/0005 已经给库加了字段，旧代码读新库通常没问题，但反过来会炸。

---

## 12. 交接检查清单

- [ ] 读过 `AGENTS.md`，知道唯一副本是 `photo-society`
- [ ] `start-local.ps1` 能起，3000 首页 200
- [ ] `/api/site/` 返回 `stats`，数字与库里一致
- [ ] `manage.py check` 无 issue；`makemigrations --check` 无待生成
- [ ] `npm run typecheck` 通过；`npm run build` 通过
- [ ] `manage.py test club.tests` 28 项通过（1 项并发按设计跳过）
- [ ] 知道 `/about` 为什么 308 到 `/members`
- [ ] 知道动效为什么不能在水合前改 class
- [ ] 知道 `db.sqlite3` 和 `storage/` 不能删
- [ ] 知道 `next start` 在本项目不可用
- [ ] 能说出现在缺的三样素材
- [ ] 知道下一步优先做「活动照片交付」

---

## 13. 文档索引与提交历史

### 13.1 文档

| 文件 | 内容 | 什么时候看 |
| --- | --- | --- |
| `AGENTS.md` | 协作硬规则 | 每次动手前 |
| `docs/HANDOVER.md` | 本文 | 接手时 |
| `DESIGN.md` | 视觉与动效规范 | 改界面前 |
| `PRODUCT.md` | 产品约束 | 定需求时 |
| `docs/PRODUCT_REVIEW.md` | 产品判断 + 改版记录 | 想知道「为什么变成这样」 |
| `docs/REVIEW-2026-10-19.md` | 2 万字全面评估（功能/审美/规范对齐） | 要做大改前 |
| `docs/ARCHITECTURE.md` | 实体关系、权限、不变量 | 改后端前 |
| `docs/API.md` | 接口清单与参数 | 联调时 |
| `docs/OPERATIONS.md` | 部署、S3、备份、换届 | 上线前 |
| `docs/MOTION.md` | 21 项交互清单 + 工程注意 | 改动效前 |
| `docs/VERIFICATION.md` | 每轮验收记录 | 怀疑「这功能到底验过没」 |
| `docs/LAUNCH_WITHOUT_ASSETS.md` | 没素材怎么上线、话术、检查清单 | 现在 |
| `design/README.md` | 原型结构决策 | 想知道栏目为什么这么分 |

### 13.2 提交历史

```
f91a0d3  Add motion evidence screenshot
415dc29  Add a full motion and interaction layer across the public site
2d2b3b8  Consolidate on photo-society: enable CI, document shared working copy
fb42413  Make the empty site presentable and add a no-assets launch guide
55acf54  Redesign public site as a contact sheet: six sections, archive codes, open applications
6d6ba06  Add product review and contact-sheet prototype before redesign
16dce84  Remove GitHub Pages preview and all static hosting adapters
```

- 分支：`main`（当前）、`redesign/contact-sheet`（已并入 main，保留备查）
- 标签：`backup/pre-contact-sheet-2026-10-19`（改版前）
- 远端：`https://github.com/alexjiang233/cdu-photography-club.git`

---

## 14. 最后三句

1. **工程不是问题，素材和定位才是。** 现在的代码足以支撑真实使用；卡住的是没人给照片、没人拍板「这网站到底为谁解决什么问题」。
2. **不要为了「更炫」再加动效。** 21 项已经到边际收益的拐点；下一步的收益在「能下载到自己的照片」这种笨功能上。
3. **改之前先看 `AGENTS.md`，回滚点已经准备好。** 大改开分支，别直接动 `main`。

交接完毕。有问题按 §13 查文档，文档没写的，看 git log。

---

## 补记 · 2026-10-21

交接后有两件事需要知道：

**1. 材料包找到了。** 程诺给的压缩包已解压到 `~/Downloads/摄影协会材料_融合版`（579 MB / 191 个文件），里面有原始 LOGO 矢量、会旗、社团手册、7 张 2024-06-04 合影原片、8 张活动海报、4 篇新闻稿，以及 2023–2026 的活动立项与总结。可用内容已整理进 `content-inbox/`（不入库，含人脸待授权），清单见 [`docs/CONTENT-INVENTORY.md`](CONTENT-INVENTORY.md)。

**2. 公开站出现了两个入口。** `/field-journal`（首页「把校园拍下来。」，五栏目，独立 nav）与 `/`（印样版，六栏目）并存，前者未挂进主导航。同时 `docs/PUBLIC_ACCESS.md` 记录了撤下前台登录与成员中心、改为访客留言的决定。**两套公开界面必须收敛成一套**，否则每一轮改版都会分叉。
