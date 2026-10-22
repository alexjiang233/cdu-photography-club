import Link from 'next/link';
import { House } from 'lucide-react';
import { GalleryHeader } from './nav';
import { serverApi } from '@/lib/server-api';
import type { Site } from '@/lib/types';
export default async function FieldJournalLayout({ children }: { children: React.ReactNode }) {
  const site = await serverApi<Site>('site/', { anonymous: true });
  return (
    <div className="exhibition-layout gallery-layout">
      <a className="fj-skip" href="#field-content">
        跳到主要内容
      </a>
      <GalleryHeader logo={site.logo_url} />
      <div id="field-content">{children}</div>
      <footer className="gl-site-footer">
        <div className="gl-footer-inner">
          <div className="gl-footer-brand" data-reveal="gallery-card" data-scroll-reveal>
            <Link
              className="gl-footer-wordmark"
              href="/#gallery-top"
              aria-label="成都大学摄影协会，返回首页"
            >
              <img
                src="/association/wordmark-university.svg"
                width="550"
                height="117"
                alt="成都大学"
              />
              <img
                src="/association/wordmark-society.svg"
                width="562"
                height="117"
                alt="摄影协会"
              />
            </Link>
            <p>Photography Society, CDU</p>
          </div>
          <nav aria-label="页脚浏览导航" data-reveal="gallery-card" data-scroll-reveal>
            <h2>浏览</h2>
            <Link href="/works">全部照片</Link>
            <Link href="/activities">活动记录</Link>
          </nav>
          <nav aria-label="页脚网站导航" data-reveal="gallery-card" data-scroll-reveal>
            <h2>关于</h2>
            <Link href="/about">关于协会</Link>
            <Link href="/privacy">作品使用与隐私</Link>
          </nav>
          <div className="gl-footer-bottom">
            <span>成都大学摄影协会 · Since 2011</span>
            <span>Chengdu, China</span>
          </div>
        </div>
      </footer>
      <Link className="gl-home-float" href="/#gallery-top">
        <House size={18} aria-hidden="true" />
        <span>回到首页</span>
      </Link>
    </div>
  );
}
