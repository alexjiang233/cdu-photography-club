# GitHub Pages 临时预览

地址：https://alexjiang233.github.io/cdu-photography-club/

这是公开的静态预览，内容来自全新内存数据库生成的示例数据。不会导出开发数据库、真实用户、内部资料或登录凭据。

支持：首页、作品与作者详情、图片大图浏览、活动与资料详情、公开示例文件下载、浏览器内搜索与筛选。登录、成员中心、投稿、报名与讨论写入暂不开放，不收集个人信息。预览通过 robots.txt 请求搜索引擎不收录，但不是访问控制。

## 构建

先按 README 安装 Python 与前端依赖，在仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe scripts/pages-demo.py
node scripts/build-pages.mjs
.\.venv\Scripts\python.exe scripts/check-pages.py
```

输出为 `.pages-build/frontend/out/`。`pages-demo.py` 重新生成 `deploy/pages/demo.json` 与临时媒体；重新生成示例时，请一并提交新快照，以保留预览使用的数据版本。

静态适配器位于 `deploy/pages/`；构建脚本在忽略的 `.pages-build/` 内复用正式前端的布局、样式、详情页和组件，替换服务器数据与需要登录的入口。正式前后端不受静态构建配置影响。

## 发布与撤下

将输出目录的内容提交到 `gh-pages` 分支根目录，并保留 `.nojekyll`。仓库 Settings → Pages 的发布源为 `gh-pages` 分支的 `/`。无需给现有 OAuth 凭据增加 workflow 权限。

`scripts/github-pages.py status` 查询发布状态；`enable` 将发布源设为该分支；`build` 重新请求构建。工具只通过 Git 已配置的凭据助手在内存中取得认证，不打印或保存凭据。

临时撤下时，在仓库 Settings → Pages 选择 Unpublish site；完整源码仍保存在 main。
