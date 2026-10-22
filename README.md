# 成都大学摄影协会网站

当前正式界面为画廊版，直接打开 **http://127.0.0.1:3000/**。

## 公开页面

- `/`：滚动照片墙、相册选片与活动预览。
- `/works`、`/works/[id]`：照片浏览、筛选、拍摄信息与灯箱。
- `/activities`、`/activities/[id]`：活动记录、查询与详情。
- `/about`：协会介绍、风格、愿景和联系信息。
- `/privacy`：作品使用与隐私说明。

公开站点没有登录、成员名录、档案、期刊或加入栏目。旧 `/field-journal` 地址仅兼容跳转，不再有第二套页面。

## 运行

项目唯一工作副本为本目录。前端 Next.js 16 / React 19，后端 Django；本地端口固定 3000 / 8000。

在项目根目录运行 `scripts/start-local.ps1` 启动，`scripts/stop-local.ps1` 停止。管理后台仍位于 `/admin/`。

## 代码与数据

- 正式前端：`frontend/src/app/(gallery)`，共用样式 `globals.css`，动效 `motion.css`。
- 后台：`backend/club`；业务发布与归档使用 `services.py`。
- 数据库：`backend/db.sqlite3`；上传文件：`backend/storage/`，均不可重置或删除。
- 照片保留原始比例和 EXIF；封面视觉样片不作为协会作品收录。
- 旧公开占位相册和资料已归档，真实照片、活动和原始文件保留。

清理范围与验证见 [正式站点说明](docs/CANONICAL_SITE.md)。较早的产品文档仅作历史参考。
