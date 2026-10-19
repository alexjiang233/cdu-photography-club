import type { Metadata } from 'next';
import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Profile, Site } from '@/lib/types';
import { DemoBadge, Empty } from '@/components/ui';
export const metadata: Metadata = { title: '关于摄影协会' };
export default async function About() {
  const [site, members] = await Promise.all([
    serverApi<Site>('site/'),
    serverApi<Profile[]>('members/'),
  ]);
  return (
    <div className="container">
      <section className="about-intro">
        <h1>
          因为喜欢摄影，
          <br />
          所以相聚。
        </h1>
        <div>
          <p>{site.introduction}</p>
          <p className="muted" style={{ marginTop: 25 }}>
            这里保存我们的作品、活动和经验。协会的真实介绍、历程与联系方式将由管理人员补充。
          </p>
        </div>
      </section>
      <section className="section-end">
        <h2 className="section-title">镜头背后的人</h2>
        {members.length ? (
          <div className="member-grid">
            {members.map((member) => (
              <Link className="member-card" key={member.id} href={`/members/${member.id}`}>
                <h3>{member.display_name}</h3>
                {member.is_demo && <DemoBadge />}
                <p>{member.bio}</p>
                {member.cohort && <p>{member.cohort}</p>}
              </Link>
            ))}
          </div>
        ) : (
          <Empty title="成员们正在整理自己的主页" />
        )}
      </section>
      <section className="join-section" id="join">
        <h2>加入摄影协会</h2>
        {site.join_instructions ? (
          <p className="prose">{site.join_instructions}</p>
        ) : (
          <p>招新方式尚未发布。正式报名入口将在协会确认后开放。</p>
        )}
        {site.contact_email && (
          <p style={{ marginTop: 15 }}>
            联系邮箱：<a href={`mailto:${site.contact_email}`}>{site.contact_email}</a>
          </p>
        )}
        <p className="muted" style={{ marginTop: 15 }}>
          已有成员账号？
          <Link className="text-link" href="/login">
            前往成员登录
          </Link>
        </p>
      </section>
      <section className="section">
        <h2 className="section-title">你可能想了解</h2>
        <details className="faq">
          <summary>没有相机，可以参与吗？</summary>
          <p>手机也可以创作和投稿。具体活动是否需要特定器材，以每次活动说明为准。</p>
        </details>
        <details className="faq">
          <summary>如何获得成员账号？</summary>
          <p>由协会管理员确认成员身份后创建账号。网站暂不开放匿名注册。</p>
        </details>
        <details className="faq">
          <summary>怎样投稿作品？</summary>
          <p>登录成员中心后创建作品系列，上传照片和图片说明，保存后提交审核。</p>
        </details>
        <details className="faq">
          <summary>在哪里查找以前的活动和资料？</summary>
          <p>活动页保留往期活动；资料库支持按年份、类别和关键词检索，内部文件需要相应权限。</p>
        </details>
      </section>
    </div>
  );
}
