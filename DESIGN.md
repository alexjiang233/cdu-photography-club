# 设计系统：影像陈列室

> 历史设计记录：用户已否定现版本的视觉与体验。本文描述当前实现，供复盘，不应当作下一版必须沿用的设计规范。

主要指导：[Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)。交互参考：[Emil design engineering](https://github.com/emilkowalski/skills/tree/main/skills/emil-design-eng)。验收参考：[Vercel web interface guidelines](https://github.com/vercel-labs/web-interface-guidelines)。

## 视觉方向
摄影协会是作品的策展者。首页用一张主照片和错落编排的作品建立印象；内页采用清晰的展签、相册和档案列表。避免营销数据墙、悬浮光球、渐变装饰与重复的功能卡片。

### 色彩
- 展墙白 `#f8f9f8`：页面背景。
- 石墨 `#222b2e`：主要文字。
- 深杉绿 `#244b43`：行动按钮、选中状态。
- 灰绿 `#66746f`：辅助信息；关键文字需通过对比度检查。
- 银灰 `#dce2df`：分隔和输入边框。
- 暖白 `#f0f2ef`：表单及次级表面。

### 字体
中文标题：本机宋体（Songti SC / Noto Serif CJK SC / SimSun）。正文：PingFang SC / Microsoft YaHei。英文大标题采用 Georgia，体现摄影刊物气质。不依赖外部字体网络请求。
标题 40–88px，内页 40–64px；正文 16px，说明 14px；表单字段至少 16px。

### 首页布局
```
文字标识      作品  活动  资料  关于       搜索  成员中心

摄影协会                    简短介绍
在日常里，看见。             查看作品 / 认识协会

                    主照片（宽幅）
                    图片说明、示例标记

精选作品                    全部作品
大幅作品        竖幅作品       小幅作品

近期活动：日期 / 标题 / 地点 / 报名状态

资料与记录：年度与分类入口
页脚
```

### 布局原则
最大内容宽度 1440px；桌面两侧留白 5vw；手机 20px。作品页使用自适应网格，详情页照片保留比例。正文左对齐。后台操作页使用紧凑表格与表单，不沿用首页的展示留白。

### 组件与动效
共享导航、按钮、表单、筛选条、内容卡、空状态、错误状态、分页、对话框。圆角只用于可操作控件，照片以自然矩形呈现。
按钮按压反馈 120ms；菜单与对话框 180–220ms，ease-out；只动画 opacity 和 transform；不做自动轮播和滚动劫持。尊重 reduced-motion，触屏不触发悬停缩放。

### 无障碍
跳过导航链接、语义化标题、可见 focus、表单 label、错误播报、原生 dialog 焦点管理；手机导航可关闭；搜索和筛选保留 URL；主要触控目标至少 44px。

## 自检
黑白摄影站容易成为通用杂志模板，因此采用低饱和深绿操作色与具有明确业务作用的活动/档案行，避免装饰性编号。视觉重点仍是作品；所有照片必须带有准确说明或示例标记。
