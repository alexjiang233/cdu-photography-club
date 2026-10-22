# -*- coding: utf-8 -*-
"""生成摄影协会「印样」原型页面。改这里，重跑即可。"""

from pathlib import Path

OUT = Path(__file__).parent

NAV = [
    ("index.html", "首页"),
    ("works.html", "作品"),
    ("events.html", "活动"),
    ("members.html", "成员"),
    ("archive.html", "档案"),
    ("join.html", "加入"),
]

WORKS = [
    ("2026-01", "留白的练习", "示例作者", "城市", "architecture.jpg", "2026.10.18"),
    ("2026-02", "山色之间", "示例作者", "自然", "nature.jpg", "2026.10.12"),
    ("2026-03", "城市的呼吸", "示例作者", "城市", "city.jpg", "2026.10.09"),
    ("2026-04", "缓慢的日常", "示例作者", "日常", "daily.jpg", "2026.10.05"),
    ("2026-05", "光经过的地方", "示例作者", "日常", "light.jpg", "2026.10.02"),
    ("2026-06", "远处与此刻", "示例作者", "自然", "water.jpg", "2026.09.28"),
]

EVENTS = [
    ("10.26", "周日", "周末走走：校园光影外拍", "14:00 集合 · 地点待协会发布", "示例活动", "demo"),
    ("11.02", "周日", "一起看照片：作品交流会", "19:00 · 学生活动中心", "示例活动", "demo"),
    ("11.09", "周日", "从曝光开始：摄影入门", "14:00 · 教室待定", "示例活动", "demo"),
]


def head(title: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 摄影协会</title>
<meta name="description" content="成都大学摄影协会：成员作品、活动记录与影像档案。">
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#main">跳到主要内容</a>"""


def header(active: str) -> str:
    items = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if label == active else ""}>{label}</a>'
        for href, label in NAV
    )
    return f"""<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html" aria-label="摄影协会首页">
      <span class="mark" aria-hidden="true"></span>
      <span><b>摄影协会</b><em>CDU PHOTOGRAPHIC ASSOCIATION</em></span>
    </a>
    <nav class="main" aria-label="主导航">
{items}
    </nav>
  </div>
</header>"""


def footer() -> str:
    return """<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <b>摄影协会</b>
        <p>成都大学文学与新闻传播学院指导。成员用相机和手机记录校园，也整理这些记录。</p>
      </div>
      <div>
        <h4>栏目</h4>
        <a href="works.html">作品</a>
        <a href="events.html">活动</a>
        <a href="members.html">成员</a>
        <a href="archive.html">档案</a>
      </div>
      <div>
        <h4>加入</h4>
        <a href="join.html">招新说明</a>
        <a href="join.html#form">在线报名</a>
        <a href="join.html#faq">常见问题</a>
        <a href="join.html#contact">联系我们</a>
      </div>
      <div>
        <h4>相关</h4>
        <a href="https://www.cdu.edu.cn/" target="_blank" rel="noopener">成都大学</a>
        <a href="https://wx.qq.com/" target="_blank" rel="noopener">微信公众号</a>
        <a href="https://www.bilibili.com/" target="_blank" rel="noopener">B 站</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 成都大学摄影协会</span>
      <span>原型演示 · 图片与文字均为示例，不代表协会真实作品</span>
    </div>
  </div>
</footer>
</body>
</html>
"""


def page(title: str, active: str, body: str) -> str:
    return head(title) + "\n" + header(active) + f'\n<main id="main">\n{body}\n</main>\n' + footer()


def frame(w, circled=False, size="4/3"):
    no, title, author, tag, img, date = w
    cls = "frame reveal" + (" circled" if circled else "")
    mark = (
        '''<svg class="mark" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path d="M52 4C24 2 5 19 5 41C5 66 26 94 52 95C78 96 96 72 95 44C94 18 74 4 46 5"/><path class="second" d="M11 63C18 85 39 95 58 92"/></svg>'''
        if circled
        else ""
    )
    return f"""      <a class="{cls}" href="work.html" style="text-decoration:none">
        <div class="box" style="aspect-ratio:{size}"><img src="assets/{img}" alt="示例作品：{title}" loading="lazy" width="1600" height="1066">{mark}</div>
        <div class="strip"><span><b class="no">{no}</b><span class="cap-title">{title}</span></span><span class="who">{author}</span></div>
      </a>"""


def event_row(e):
    day, week, title, meta, chip, kind = e
    return f"""      <article class="event">
        <div class="date"><b>{day}</b><span>{week}</span></div>
        <div>
          <h3>{title}</h3>
          <p class="meta">{meta}</p>
        </div>
        <div class="side"><span class="chip {kind}">{chip}</span><span class="go" aria-hidden="true">→</span></div>
      </article>"""


# ---------------------------------------------------------------- 首页
home = f"""<section class="wrap hero">
  <div class="hero-copy">
    <p class="eyebrow">成都大学 · 摄影协会</p>
    <h1>把照片<br>留下来。</h1>
    <p class="lead">成员拍的照片、办过的活动、还没整理完的档案，都放在这里。没有推荐算法，只有照片，和拍照片的人。</p>
    <div class="actions">
      <a class="btn" href="works.html">看作品</a>
      <a class="link" href="join.html">加入我们 <span class="arw">↗</span></a>
    </div>
  </div>
  <figure class="cover frame reveal">
    <a href="work.html"><div class="box"><img src="assets/architecture.jpg" alt="示例作品：留白的练习" width="1600" height="1066" fetchpriority="high"></div></a>
    <figcaption class="strip"><span><b class="no">2026-01</b>留白的练习</span><span>示例作者</span></figcaption>
    <p class="credit">示例图片 · 待替换为协会成员作品</p>
  </figure>
</section>

<section class="wrap stats" aria-label="当前收录">
  <div class="stat"><b>06</b><span>组作品</span></div>
  <div class="stat"><b>06</b><span>张照片</span></div>
  <div class="stat"><b>03</b><span>场活动</span></div>
  <div class="stat"><b>01</b><span>份档案</span></div>
</section>

<section class="wrap section">
  <div class="sec-head">
    <div>
      <p class="eyebrow">Contact sheet / 本期印样</p>
      <h2>最近放上来的照片</h2>
    </div>
    <a class="link" href="works.html">全部作品 06 组 <span class="arw">↗</span></a>
  </div>
  <div class="sheet">
{chr(10).join(frame(w, circled=(i == 0)) for i, w in enumerate(WORKS))}
  </div>
  <p class="footnote">红圈是这一期选中的一张。第 07 格，留给下一次外拍。</p>
</section>

<section class="alt">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Upcoming / 近期</p>
        <h2>接下来要发生的事</h2>
      </div>
      <a class="link" href="events.html">全部活动 <span class="arw">↗</span></a>
    </div>
{chr(10).join(event_row(e) for e in EVENTS)}
    <p class="footnote">示例活动不开放真实报名。正式活动发布后会显示名额与截止时间。</p>
  </div>
</section>

<section class="wrap section">
  <div class="members-layout">
    <aside>
      <p class="eyebrow">People / 成员</p>
      <h2>照片后面的人</h2>
      <p class="lead">协会不只有作品。谁在拍、拍了多久、擅长什么，都写在这里。</p>
      <a class="link" href="members.html" style="margin-top:18px">全部成员 <span class="arw">↗</span></a>
    </aside>
    <article class="profile">
      <div class="profile-head">
        <span class="monogram big">示</span>
        <div><h3>示例作者</h3><p class="role">摄影组 · 2026 级 · 加入于 2026.09</p></div>
        <span class="num">作品 06 组</span>
      </div>
      <blockquote>“一句话自我介绍由成员本人填写，不超过 24 字。写你真正在拍的东西。”</blockquote>
      <dl class="profile-meta">
        <div><dt>常用器材</dt><dd>由本人填写</dd></div>
        <div><dt>常拍</dt><dd>城市 / 日常</dd></div>
        <div><dt>主页</dt><dd><a href="members.html">查看作品 →</a></dd></div>
      </dl>
    </article>
  </div>
</section>

<section class="dark">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Archive / 档案</p>
        <h2>影像之外，还有资料。</h2>
      </div>
      <a class="link" href="archive.html" style="color:#f3efe6">进入档案 <span class="arw">↗</span></a>
    </div>
    <div class="year">
      <b>2026<small>1 份 · 照片 6 张</small></b>
      <div>
        <div class="doc"><span class="t">摄影入门与资料归档说明</span><span class="m">教程 / v1 / 2026.10</span></div>
        <div class="doc"><span class="t">校园光影外拍 · 活动记录</span><span class="m">策划 / 待整理</span></div>
      </div>
    </div>
    <div class="year">
      <b>2025<small>待归档</small></b>
      <p class="pending">这一年的文件还没有人整理。换届交接时，请把策划、名单、成片放进来。</p>
    </div>
    <div class="year">
      <b>2024<small>待归档</small></b>
      <p class="pending">空着也没关系。档案允许缺页，但不应该假装完整。</p>
    </div>
  </div>
</section>

<section class="join">
  <div class="wrap join-grid">
    <div>
      <p class="eyebrow">Join / 招新</p>
      <h2 style="margin:14px 0 18px">每年 9–10 月，<br>我们收一次人。</h2>
      <p class="lead">不限器材，不限基础。手机、卡片机、单反都行；不会后期也没关系，协会里有人教。</p>
      <div class="actions"><a class="btn" href="join.html">看招新说明</a></div>
    </div>
    <ol class="steps">
      <li><b>01</b><span><strong>线上报名</strong><br>填一份表，说说你想拍什么。</span></li>
      <li><b>02</b><span><strong>带三张照片来聊</strong><br>不评好坏，只聊你为什么拍它们。</span></li>
      <li><b>03</b><span><strong>入会</strong><br>进群，领协会的拍摄安排。</span></li>
    </ol>
  </div>
</section>"""

# ---------------------------------------------------------------- 作品
works_body = f"""<section class="wrap page-head">
  <p class="eyebrow">Works / 作品</p>
  <h1>作品</h1>
  <p class="lead">按发布时间排列。每张照片保留原始比例，不做统一裁剪——构图是拍摄者的，不是版式的。</p>
  <div class="filters">
    <a class="on" href="works.html">全部</a>
    <a href="works.html">自然</a>
    <a href="works.html">城市</a>
    <a href="works.html">日常</a>
    <a href="works.html">人像</a>
    <span class="count">6 组 / 6 张</span>
  </div>
  <div class="sheet">
{chr(10).join(frame(w) for w in WORKS)}
  </div>
  <p class="footnote">点击任意一组进入详情：大图、图注、拍摄信息，以及这组照片关联的活动。</p>
</section>

<section class="wrap section">
  <div class="sec-head">
    <div><p class="eyebrow">How it works</p><h2>一组作品，四种读法</h2></div>
  </div>
  <div class="members cols-4">
    <div class="member"><h3>照片</h3><p>保留原始比例，点开看大图，键盘左右切换。</p></div>
    <div class="member"><h3>图注</h3><p>每张都有说明。没有说明的照片不允许发布。</p></div>
    <div class="member"><h3>拍摄信息</h3><p>机身、镜头、光圈、快门、ISO、地点、时间。</p></div>
    <div class="member"><h3>关联</h3><p>这组照片属于哪次活动、哪位作者。</p></div>
  </div>
</section>"""

# ---------------------------------------------------------------- 活动
events_body = f"""<section class="wrap page-head">
  <p class="eyebrow">Events / 活动</p>
  <h1>活动</h1>
  <p class="lead">外拍、看片会、入门课。活动结束后，照片和资料会归档到对应年份，不用再翻聊天记录。</p>
</section>

<section class="wrap section" style="padding-top:48px">
  <div class="sec-head">
    <div><p class="eyebrow">Upcoming / 即将开始</p><h2>最近三场</h2></div>
    <span class="count" style="font:400 11px var(--mono);color:var(--ink-2)">按时间由近到远</span>
  </div>
{chr(10).join(event_row(e) for e in EVENTS)}
</section>

<section class="wrap section">
  <div class="sec-head">
    <div><p class="eyebrow">Past / 往期</p><h2>活动记录</h2></div>
  </div>
  <div class="pending-row" style="max-width:640px">
    还没有往期活动。<br>
    第一次活动结束后，报名名单、现场照片、复盘文档会自动归到这一年。
  </div>
</section>

<section class="wrap section">
  <div class="sec-head">
    <div><p class="eyebrow">How an event works</p><h2>一场活动，从报名到归档</h2></div>
  </div>
  <div class="members cols-3">
    <div class="member"><span class="role">01 / 报名</span><h3>名额与截止</h3><p>报名占一个名额，取消会释放。名单里的联系方式只有负责人能看到。</p></div>
    <div class="member"><span class="role">02 / 现场</span><h3>拍摄与交付</h3><p>活动结束后，参与成员把照片传进同一场活动；参与者可以按作者找，也可以打包下载。</p></div>
    <div class="member"><span class="role">03 / 归档</span><h3>成片与文档</h3><p>成片、策划、复盘归进当年档案。下一届不用再翻群聊记录。</p></div>
  </div>
</section>"""

# ---------------------------------------------------------------- 成员
members_body = """<section class="wrap page-head">
  <p class="eyebrow">Members / 成员</p>
  <h1>成员</h1>
  <p class="lead">协会按组分工，但拍什么由自己决定。成员主页由本人填写；毕业撤权后，署名仍留在作品上。</p>
</section>

<section class="wrap section" style="padding-top:44px">
  <div class="members">
    <article class="member">
      <div class="top"><span class="monogram">示</span><div><h3>示例作者</h3><p class="role">摄影组 / 2026 级</p></div></div>
      <p>“一句话自我介绍由成员本人填写。”</p>
      <span class="num">作品 6 组 · 加入 2026.09</span>
    </article>
    <div class="member empty"><span>成员 02<br>等待本人填写</span></div>
    <div class="member empty"><span>成员 03<br>等待本人填写</span></div>
  </div>
  <p class="footnote">不显示手机号、学号、宿舍等个人信息。联系方式只在报名和活动名单里出现。</p>
</section>

<section class="wrap section">
  <div class="sec-head"><div><p class="eyebrow">Structure</p><h2>协会怎么分工</h2></div></div>
  <div class="members cols-3">
    <div class="member"><h3>摄影组</h3><p>外拍、活动跟拍、作品整理。器材不限。</p></div>
    <div class="member"><h3>后期组</h3><p>选片、调色、输出。也负责活动成片的交付。</p></div>
    <div class="member"><h3>运营组</h3><p>公众号、展览、招新与档案整理。</p></div>
  </div>
</section>"""

# ---------------------------------------------------------------- 档案
docs_2026 = [
    ("摄影入门与资料归档说明", "教程", "v1", "2026.10.19", "下载"),
    ("校园光影外拍 · 活动策划", "活动策划", "v2", "2026.10.12", "下载"),
    ("2026 学年干事名单", "换届交接", "v1", "2026.09.30", "下载"),
]
doc_rows = "\n".join(
    f'      <div class="doc-row"><span class="title">{t}</span><span class="meta">{c}</span><span class="meta">{v} · {d}</span><a class="dl" href="#">{dl}</a></div>'
    for t, c, v, d, dl in docs_2026
)

archive_body = f"""<section class="wrap page-head">
  <p class="eyebrow">Archive / 档案</p>
  <h1>档案</h1>
  <p class="lead">教程、策划、交接文档、刊物。按年份存放，可以按类别和关键词找；内部文件需要成员登录。</p>
</section>

<section class="wrap section" style="padding-top:44px">
  <div class="archive-layout">
    <nav class="year-index" aria-label="年份">
      <a href="#y2026">2026 · 3</a>
      <a href="#y2025">2025 · 待归档</a>
      <a href="#y2024">2024 · 待归档</a>
      <a href="#y2023">2023 · 待归档</a>
    </nav>
    <div>
      <div class="archive-year" id="y2026">
        <h2>2026</h2>
        <p class="sub">3 份 · 公开 2 / 内部 1</p>
{doc_rows}
      </div>
      <div class="archive-year" id="y2025">
        <h2>2025</h2>
        <p class="sub">待归档</p>
        <div class="pending-row">这一年的文件还没有上传。换届时请把活动策划、报名名单、成片和复盘放进来。</div>
      </div>
      <div class="archive-year" id="y2024">
        <h2>2024</h2>
        <p class="sub">待归档</p>
        <div class="pending-row">档案允许缺页。补齐之前，这里保持空白，不编造记录。</div>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="sec-head"><div><p class="eyebrow">Rules</p><h2>档案的三条规矩</h2></div></div>
  <div class="members cols-3">
    <div class="member"><h3>只增不改</h3><p>新版本另存，旧版本保留。已发布的内容不会因为更新而消失。</p></div>
    <div class="member"><h3>权限随内容</h3><p>公开资料谁都能下；内部资料要成员身份；原片只有本人和管理员能取。</p></div>
    <div class="member"><h3>交接优先</h3><p>每届换届必须留下：账号、策划、名单、素材位置。</p></div>
  </div>
</section>"""

# ---------------------------------------------------------------- 加入
faq = [
    ("没有相机，可以加入吗？", "可以。手机也是相机。协会的活动不限定器材，外拍前会说明这次适合带什么。"),
    ("需要会后期吗？", "不需要。后期组会做入门分享；你也可以只拍不修，把原片交给后期组一起处理。"),
    ("招新时间是什么时候？", "每学年 9–10 月，具体日期以公众号和校内公告为准。错过招新可以单独联系，参加下一次活动。"),
    ("报名表里要填什么？", "姓名、学院、年级、联系方式、常用器材、作品链接（没有可以空着），以及你想拍什么。"),
    ("成员要做什么？", "每学期至少参加两次活动，提交一组作品。其他时间自由安排。"),
]
faq_html = "\n".join(
    f'      <details><summary>{q}</summary><p>{a}</p></details>' for q, a in faq
)

join_body = f"""<section class="wrap page-head">
  <p class="eyebrow">Join / 加入</p>
  <h1>加入摄影协会</h1>
  <p class="lead">我们不看器材，也不看基础。只看你愿不愿意认真拍一点东西，并且把它留下来。</p>
</section>

<section class="wrap section" style="padding-top:44px">
  <div class="members cols-3">
    <div class="member"><span class="role">对象</span><h3>成都大学在校生</h3><p>本科、研究生都可以。不限学院与年级。</p></div>
    <div class="member"><span class="role">时间</span><h3>每学年 9–10 月</h3><p>以公众号与校内公告为准，错过可单独联系。</p></div>
    <div class="member"><span class="role">地点</span><h3>学生活动中心</h3><p>具体教室在报名后通知，不公开个人联系方式。</p></div>
  </div>
</section>

<section class="wrap section" id="form">
  <div class="sec-head"><div><p class="eyebrow">Application / 报名</p><h2>填一份表</h2></div></div>
  <form class="note" action="#" method="post">
    <div class="form-grid">
      <div class="field"><label for="name">姓名<em>*</em></label><input id="name" name="name" required autocomplete="name" placeholder="你的名字"></div>
      <div class="field"><label for="college">学院与专业<em>*</em></label><input id="college" name="college" required placeholder="例如：文学与新闻传播学院 网络与新媒体"></div>
      <div class="field"><label for="grade">年级<em>*</em></label>
        <select id="grade" name="grade"><option>2026 级</option><option>2025 级</option><option>2024 级</option><option>研究生</option></select>
      </div>
      <div class="field"><label for="contact">手机或微信<em>*</em></label><input id="contact" name="contact" required autocomplete="tel" placeholder="只用于联系你"></div>
      <div class="field"><label for="gear">常用器材</label><input id="gear" name="gear" placeholder="手机 / 卡片机 / 单反 / 微单，没有也可以"></div>
      <div class="field"><label for="portfolio">作品链接</label><input id="portfolio" name="portfolio" placeholder="网盘、相册或社交主页，没有可以空着"></div>
      <div class="field full"><label for="why">你想拍什么</label><textarea id="why" name="why" placeholder="一句话就够。比如：想拍晚上还亮着灯的教学楼。"></textarea></div>
    </div>
    <div class="form-foot">
      <button class="btn" type="submit">提交报名</button>
      <span class="hint">原型表单，不会真的提交。正式版会写明隐私说明与处理时限。</span>
    </div>
  </form>
</section>

<section class="wrap section" id="faq">
  <div class="sec-head"><div><p class="eyebrow">FAQ / 常见问题</p><h2>你可能想问</h2></div></div>
  <div class="faq">
{faq_html}
  </div>
</section>

<section class="join" id="contact" style="margin-top:64px">
  <div class="wrap join-grid">
    <div>
      <p class="eyebrow">Contact</p>
      <h2 style="margin:14px 0 18px">找不到答案，<br>直接问。</h2>
      <p class="lead">招新群里有人在。也可以发邮件，我们会在一周内回复。</p>
    </div>
    <ol class="steps">
      <li><b>01</b><span><strong>招新 QQ 群</strong><br>群号待协会公布</span></li>
      <li><b>02</b><span><strong>邮箱</strong><br>待协会公布</span></li>
      <li><b>03</b><span><strong>线下</strong><br>学生活动中心，活动日现场</span></li>
    </ol>
  </div>
</section>"""

related = "\n".join(
    f'''    <a class="frame" href="work.html"><div class="box"><img src="assets/{img}" alt="示例作品：{title}" loading="lazy" width="1600" height="1066"></div><div class="strip"><span><b class="no">{no}</b><span class="cap-title">{title}</span></span><span class="who">{author}</span></div></a>'''
    for no, title, author, tag, img, date in WORKS[1:4]
)

work_body = f"""<section class="wrap page-head">
  <nav class="crumbs"><a href="works.html">作品</a><span>/</span><span>2026-01</span></nav>
  <h1 style="margin-top:16px">留白的练习</h1>
  <p class="work-meta">示例作者 · 2026.10.18 · 1 张 · 关联活动：校园光影外拍</p>
</section>

<section class="wrap">
  <figure class="frame big">
    <div class="box" style="aspect-ratio:3/2"><img src="assets/architecture.jpg" alt="示例作品：留白的练习" width="1600" height="1066" fetchpriority="high"></div>
    <figcaption class="strip"><span><b class="no">2026-01</b>留白的练习</span><span>示例作者</span></figcaption>
  </figure>
  <div class="work-body">
    <div>
      <p class="prose">示例说明：这张照片在校园里拍摄。正式使用时，这里放作者自己写的创作说明——在哪拍的、为什么按下快门、想留下什么。一段就够，不必抒情。</p>
      <p class="prose">图注：示例图注，说明画面里发生了什么。</p>
    </div>
    <dl class="spec">
      <div><dt>机身</dt><dd>示例参数</dd></div>
      <div><dt>镜头</dt><dd>示例参数</dd></div>
      <div><dt>焦距</dt><dd>35 mm</dd></div>
      <div><dt>光圈</dt><dd>f/4</dd></div>
      <div><dt>快门</dt><dd>1/250 s</dd></div>
      <div><dt>ISO</dt><dd>200</dd></div>
      <div><dt>地点</dt><dd>示例地点</dd></div>
      <div><dt>授权</dt><dd>作者授权展示</dd></div>
    </dl>
  </div>
  <p class="footnote">拍摄参数从原片读取；没有的字段留空，不编造。原片不公开下载。</p>
</section>

<section class="wrap section">
  <div class="sec-head">
    <div><p class="eyebrow">Same event</p><h2>同一场活动的其他照片</h2></div>
    <a class="link" href="events.html">看这场活动 <span class="arw">↗</span></a>
  </div>
  <div class="sheet">
{related}
  </div>
</section>

<nav class="wrap pager" aria-label="作品翻页">
  <a class="link" href="works.html">← 上一组</a>
  <a class="link" href="works.html">全部作品</a>
  <a class="link" href="work.html">下一组 →</a>
</nav>"""

PAGES = [
    ("index.html", "首页", "首页", home),
    ("works.html", "作品", "作品", works_body),
    ("events.html", "活动", "活动", events_body),
    ("members.html", "成员", "成员", members_body),
    ("archive.html", "档案", "档案", archive_body),
    ("join.html", "加入", "加入", join_body),
    ("work.html", "作品详情", "作品", work_body),
]

for filename, title, active, body in PAGES:
    (OUT / filename).write_text(page(title, active, body), encoding="utf-8")
    print("wrote", filename)
