import { serverApi } from '@/lib/server-api';
import type { Site } from '@/lib/types';
import { associationGroupPhoto } from '../association';
export const metadata = {
  title: '关于协会',
  description: '认识成都大学摄影协会：我们是谁、我们的风格与愿景。',
};
export default async function About() {
  const site = await serverApi<Site>('site/', { anonymous: true });
  return (
    <div className="gl-page gl-about-page">
      <header className="gl-page-heading">
        <p>Photography Society, CDU / About</p>
        <h1>因为摄影，<br />相聚在这里。</h1>
      </header>
      <div className="gl-about-lead">
        <figure data-reveal="gallery-print" data-scroll-reveal>
          <img {...associationGroupPhoto} fetchPriority="high" />
        </figure>
        <section className="gl-about-who" data-reveal="gallery-card" data-scroll-reveal>
          <p className="gl-about-label">01 / Who we are</p>
          <h2>我们是谁</h2>
          <p className="gl-about-intro">一群喜欢摄影的人。</p>
          <p>我们是成都大学摄影协会，成立于 2011 年，挂靠文学与新闻传播学院。</p>
          <p>因为喜欢摄影聚在一起，平时聊相机、聊照片，也约着出去拍照。</p>
        </section>
      </div>
      <div className="gl-about-statements">
        <section data-reveal="gallery-card" data-scroll-reveal>
          <div className="gl-about-section-title">
            <p className="gl-about-label">02 / Our approach</p>
            <h2>我们的风格</h2>
          </div>
          <div className="gl-about-section-copy">
            <p className="gl-about-intro">随意一点，<br />亲近一点。</p>
            <p>聊相机，也聊照片。带着各自的兴趣来，看看彼此眼里的世界。</p>
          </div>
        </section>
        <section data-reveal="gallery-card" data-scroll-reveal>
          <div className="gl-about-section-title">
            <p className="gl-about-label">03 / Looking ahead</p>
            <h2>我们的愿景</h2>
          </div>
          <div className="gl-about-section-copy">
            <p className="gl-about-intro">让喜欢摄影的人，<br />更容易遇见彼此。</p>
            <p>留下值得回看的照片，也让聊起的外拍和旅行，有一天真正出发。</p>
          </div>
        </section>
      </div>
      {(site.contact_qr_url || site.contact_email) && (
        <section className="gl-about-contact" data-reveal="gallery-card" data-scroll-reveal>
          <h2>联系协会</h2>
          {site.contact_qr_url && (
            <img src={site.contact_qr_url} width="160" height="160" alt="摄影协会联系二维码" />
          )}
          {site.contact_email && <a href={`mailto:${site.contact_email}`}>{site.contact_email}</a>}
          {site.join_instructions && (
            <p className="wall-contact-instructions">{site.join_instructions}</p>
          )}
        </section>
      )}
    </div>
  );
}
