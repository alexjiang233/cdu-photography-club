# 部署、备份与换届交接

## 当前边界

代码与本地预览已经建立。已使用官方发行商提供的 PostgreSQL 17.11 便携版完成真实数据库测试、并发锁验证与独立数据库恢复，没有注册系统服务。当前机器没有 Docker、Redis、ClamAV 或公网域名；容器整套部署、生产队列、扫描、SMTP 与实际证书签发仍需要在服务器执行验收。

正式部署必须使用 `DEBUG=0`，配置 PostgreSQL、长随机密钥、正确域名及 CSRF 来源。缺少关键配置会拒绝启动。开发默认使用 SQLite、本地存储、同步图片任务和控制台邮件，仅用于本地预览。

## 正式部署步骤

1. 准备 Linux 服务器、Docker Compose、域名 DNS。仅开放公网 80/443，SSH 限制为管理员来源。
2. 将本目录作为独立项目存放。复制 `.env.example` 为 `.env`，填写以下配置：
   - `DEBUG=0`。
   - `DJANGO_SECRET_KEY`：至少 50 位随机值，使用安全随机生成器。
   - `SITE_DOMAIN`：真实域名，例如 `photo.your-school.example`。
   - `ALLOWED_HOSTS`：真实域名及 `backend,localhost,127.0.0.1`。
   - `CSRF_TRUSTED_ORIGINS=https://你的域名`。
   - PostgreSQL 随机密码；禁止复用管理员登录密码。
   - SMTP 配置，或明确保持邮件恢复未开放。
3. 保护 `.env` 为仅部署人员可读。建立 `backups/`，允许容器 app 用户写入（镜像默认 UID 1000），不要开放公共下载。
4. `docker compose build`；然后 `docker compose up -d db redis antivirus-updater`。
5. `docker compose run --rm backend python manage.py migrate`。
6. `docker compose run --rm backend python manage.py collectstatic --noinput`。
7. `docker compose run --rm backend python manage.py bootstrap_roles`。
8. `docker compose run --rm backend python manage.py createsuperuser`，由本人输入密码。
9. `docker compose run --rm backend python manage.py enroll_admin_mfa 你的账号`，在可信验证器中绑定 TOTP。输出包含敏感绑定密钥，不录屏、不保存日志。
10. 确认 ClamAV 病毒库已成功更新且可读；扫描不可用时文件上传将拒绝处理。
11. `docker compose up -d`；Caddy 自动申请证书。
12. `docker compose exec backend python manage.py check --deploy`，检查服务健康、真实登录、邮件、权限与文件流程。

管理端用户需要 `is_staff`，并拥有管理组权限；只有系统管理员负责用户与权限分配。生产 API 的 staff 登录和后台都需要 TOTP。丢失验证器时由服务器管理员核实身份后重新绑定，不能暴露免验证恢复入口。

## S3 与图片

默认使用 Docker 私有文件卷，便于首次部署。若启用 S3，配置私有桶、最小权限账号和受控 Endpoint；禁止对象的匿名读取。后端文件网关负责授权与输出，存储键不会直接返回普通客户端。

当前原片最长边不缩放保存，展示图去 EXIF。没有公共 CDN，撤回内容后网关立即拒绝新请求。若部署 CDN，禁止缓存 `/api/`、`/admin/` 和成员页面。后续如改为公开展示图缓存，需要实现撤回清除与权限降级处理。

## 备份与恢复

备份命令不会删除历史备份：

```bash
docker compose exec backend python manage.py backup_site --output /backups
```

备份包含数据库、私有媒体、SHA-256 清单，不包含 `.env` 与认证器外部恢复信息；这些配置应由管理员单独加密保存。备份含账号密码哈希、联系人和原片，必须加密并存放到独立位置。

命令使用 PostgreSQL `pg_dump` 或 SQLite 在线备份接口；媒体采用不可变文件键，因此数据库快照之后新增的媒体不会破坏快照引用。禁止在备份过程中人为删除媒体。S3 备份需要列出和读取权限；对象存储还应开启版本控制与保留策略。

校验：`python scripts/verify-backup.py /绝对路径/备份目录`。校验和只能证明文件未改变，不能替代恢复演练。

如果系统存在多个 PostgreSQL 客户端，可用 `backup_site --pg-dump-bin /绝对路径/pg_dump` 明确指定匹配版本的工具。命令会检查备份格式头，只有数据库与媒体全部完成后才写入清单。

恢复演练应在空的隔离环境执行：

1. 复制备份到隔离目录并校验，保留生产原件。
2. PostgreSQL：创建空数据库，使用匹配版本的 `pg_restore --no-owner --dbname=恢复数据库 database.dump`；不得对生产库执行 `--clean`。SQLite：复制 `database.sqlite3` 到隔离实例。
3. 将 `media/` 复制至隔离实例的私有存储根目录；S3 恢复到独立测试桶，不覆盖生产桶。
4. 加载相应密钥配置，执行迁移检查，打开作品、下载资料、核对记录数量。
5. 定期做一次完整演练；正式切换前停止写入、保留当前快照，由管理员确认恢复目标。

建议每天备份、保留每日 14 份与每周 8 份；这是建议策略，当前没有擅自在用户机器创建计划任务。管理员应在服务器中安排，并配置失败告警。未经演练，不应承诺恢复时间。

## 监控与更新

- 监控站点可达性、`/api/health/`、容器健康、磁盘用量、队列积压及备份是否按时生成。
- 当前只有健康接口、容器健康检查和日志接入点，没有实际配置外部告警接收方。
- 反向代理日志不记录查询参数，避免密码重置 token 出现在常规访问日志。
- 固定前后端依赖锁；更新先在测试环境跑流程与权限测试，再备份、迁移、发布。
- 服务器与 ClamAV 病毒库定期更新；站点上线前为实际资源量设置存储与带宽告警。

## 换届清单

移交域名、服务器、代码仓库、私有文件存储、邮件服务、备份位置和验证器恢复流程。逐一核对账号归属、续费日期及至少两位维护人员。撤销离任者后台权限和有效成员身份，保留作品署名；不要共用一个超级管理员账号。

由新维护人员独立完成一次发布与一次隔离恢复，才算交接完成。
