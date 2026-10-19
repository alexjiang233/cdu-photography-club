# API 约定

统一前缀 `/api/`，JSON；文件上传使用 multipart。URL 保留末尾 `/`。列表分页每页 24 条，返回 `count / next / previous / results`；`page` 选择页码。权限不足返回 403 或隐藏对象的 404，字段错误返回 400。

## 身份

| 路径 | 方法 | 作用 |
| --- | --- | --- |
| `auth/session/` | GET | 当前身份，初始化 CSRF Cookie 并返回 token |
| `auth/login/` | POST | `username, password, otp?`；生产 staff 账号需要 TOTP |
| `auth/logout/` | POST | 清除会话 |
| `auth/account/` | PATCH | `display_name, bio, cohort, is_public` |
| `auth/account/` | POST | `current_password, new_password` |
| `auth/reset-password/` | POST | 申请：`email`；重置：`uid, token, password` |

登录和密码重置即使匿名也要求 CSRF。所有其他会话写操作同样要求 `X-CSRFToken`。不存在公开注册入口。

## 内容

| 路径 | 方法 | 作用 |
| --- | --- | --- |
| `collections/` | GET / POST | 可访问作品 / 成员新建草稿 |
| `collections/{id}/` | GET / PATCH | 详情 / 编辑草稿 |
| `collections/{id}/photos/` | POST | `asset_id, caption, position?` |
| `collections/{id}/update-photo/` | POST | `photo_id, caption, position?` |
| `collections/{id}/remove-photo/` | POST | `photo_id`，只移除作品引用 |
| `events/` | GET / POST | 活动查询 / 获授权人员建草稿 |
| `events/{id}/` | GET / PATCH | 详情 / 编辑草稿 |
| `events/{id}/register/` | POST | `contact, note?`，有效成员报名 |
| `events/{id}/cancel-registration/` | POST | 本人取消报名 |
| `events/{id}/registrations/` | GET | 负责人/编辑查看名单 |
| `documents/` | GET / POST | 可访问资料 / 获授权人员建草稿 |
| `documents/{id}/` | GET / PATCH | 资料与历史版本 / 编辑草稿 |
| `documents/{id}/versions/` | POST | `asset_id, note?`，生成下一版本 |

三类内容均支持 `/{id}/workflow/` POST，参数 `action`：`submit / publish / return / revise / archive`；退回需填写 `note`。

作品与活动均支持 `/{id}/comments/` GET / POST，创建参数 `text`。新讨论等待后台审核；作者可以看到自己的待审核内容。

查询参数：三类内容支持 `q, tag, mine=1`；作品支持 `featured=1, author, event`；资料支持 `year, category, event`。搜索仅查询标题、简介和标签，未实现 PDF 正文检索。

## 文件与网站

| 路径 | 方法 | 作用 |
| --- | --- | --- |
| `upload/` | GET / POST | GET 分页查询本人的图片，`collection` 排除该作品已关联图片；POST `file` 上传 |
| `assets/{id}/` | GET | 本人/文件管理员查询处理状态 |
| `assets/{id}/thumbnail/` | GET | 通过内容权限校验的缩略图 |
| `assets/{id}/display/` | GET | 通过内容权限校验的展示图 |
| `assets/{id}/download/` | GET | 原文件授权下载，响应为附件 |
| `site/` | GET | 网站介绍、联系方式、Logo 和标签 |
| `members/` | GET | 公开作者档案 |
| `members/{id}/` | GET | 单个公开作者档案 |
| `dashboard/` | GET / POST | 本人作品/报名/通知；POST 标记通知已读 |
| `health/` | GET | 最小数据库健康信号，无敏感配置 |

文件链接不是永久公共链接：下载/展示时重新检查权限。图片 URL 的版本参数为内容校验值前缀，只用于区分版本，不用于鉴权。
