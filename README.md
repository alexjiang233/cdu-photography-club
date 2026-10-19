# 摄影协会网站

> 当前工程快照，尚未上线。现有产品价值与视觉方案已被提出明确质疑，不能作为完成的官网发布。保留工程便于继续评估和修改，具体反馈见 [产品复盘](docs/PRODUCT_REVIEW.md)。

摄影协会的作品展示、成员投稿、活动报名与资料归档系统。Next.js 前端 + Django API/后台；开发使用 SQLite 与本地私有文件，正式部署使用 PostgreSQL，可选私有 S3 对象存储。

## 已贯通的功能

- 公开首页、作品筛选、作品详情与可键盘操作的大图浏览。
- 作者公开主页；公开档案与登录身份分离，成员退出后可保留署名。
- 活动详情、报名、名额限制、重复报名防护、取消报名、负责人名单查看。
- 资料按年份、类别和关键词检索；历史版本、授权下载与操作审计。
- 成员登录、修改资料与密码、密码重置接口、消息与报名记录。
- 作品草稿、照片上传与排序/说明、中断后找回上传图片、提交审核、发布、退回、撤回与归档。
- 管理后台维护作品、活动、文件、成员、网站名称/介绍/Logo/联系方式。
- 正式环境管理员 TOTP、多层权限、CSRF、限速、图片安全解码与去 EXIF、私有文件网关、生产文档扫描。
- 生产容器配置、备份校验工具、PostgreSQL 并发测试与 CI 配置。

自动检查目前以模板保存为 `deploy/github-actions-checks.yml`，尚未启用。当前上传使用的 GitHub 授权没有 `workflow` 权限；有需要时由仓库所有者通过获授权的方式将模板放到 `.github/workflows/checks.yml`。

## 本地运行（Windows）

需要 Python 3.12+ 与 Node.js 20.9+。首次克隆后请按以下步骤安装依赖；本地数据库、账号、原片与依赖目录不在仓库中。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
Set-Location frontend
npm.cmd ci
Set-Location ..
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py bootstrap_roles
.\.venv\Scripts\python.exe backend\manage.py collectstatic --noinput
.\scripts\start-local.ps1
```

打开 <http://127.0.0.1:3000>。后台 <http://127.0.0.1:3000/admin/>。

如需示例内容：运行 `python scripts/fetch-demo-assets.py` 下载示例照片，然后运行 `python backend/manage.py seed_demo`。已有文件时不会重复下载。种子命令不创建可登录账号。

创建自己的管理员：

```powershell
.\.venv\Scripts\python.exe backend\manage.py createsuperuser
```

请自行输入邮箱与密码；仓库不包含默认管理员密码。成员账号通过后台建立，再在“成员档案”中启用有效成员身份。编辑/负责人需要勾选用户的“工作人员状态”并分配相应管理组。

停止本项目启动的服务：`scripts/stop-local.ps1`。`start-local.ps1 -Production` 仅表示使用前端生产构建预览，后端仍是开发服务器，不能用于公网。

## 工程边界

```text
frontend/src/app/         页面与路由
frontend/src/components/ 可复用交互、表单与展示组件
frontend/src/lib/        类型、客户端/服务端 API 与格式化
backend/club/api/        HTTP 适配：认证、内容、文件、公开信息
backend/club/models.py   数据模型与数据库约束
backend/club/services.py 审核状态机、报名事务、审计与通知
backend/club/permissions.py 对象级可见性和操作权限
backend/club/uploads.py  文件校验与入库
backend/club/tasks.py    图片处理后台任务
backend/club/storage.py  私有本地/S3 文件适配
backend/club/admin.py    管理界面，复用业务状态机
backend/club/tests/      流程、安全和并发测试
deploy/                 HTTPS 网关、反向代理、容器构建
docs/                   架构、接口、运维与验收记录
```

内容只有一个正式归属。首页、作者页、活动页通过关联引用作品与文件。修改业务规则时应修改 `services.py` 或权限层，不能在页面或后台另写一份规则。

## 验证

```powershell
.\.venv\Scripts\python.exe backend\manage.py test club.tests
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
Set-Location frontend
npm.cmd run typecheck
npm.cmd run build
```

并发名额测试需要 PostgreSQL；SQLite 本地测试会明确跳过。正式配置、备份恢复和上线前的外部依赖见 [运维说明](docs/OPERATIONS.md)，验证边界见 [验收记录](docs/VERIFICATION.md)。

## 尚需协会提供 / 明确保留的入口

- 协会 Logo、真实照片与授权、介绍、成员资料、招新方式和联系邮箱。
- 公网域名、服务器、邮件服务、备份位置和实际运营管理人员。
- 器材借用、RAW 大文件、PDF 正文检索/OCR 暂未开放；入口说明在成员中心。
- 示例照片来自 Unsplash，来源记录在 `demo-assets/credits.json`，不得作为协会成员作品宣传。

设计规范：[DESIGN.md](DESIGN.md)。产品约束：[PRODUCT.md](PRODUCT.md)。
