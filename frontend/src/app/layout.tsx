import type { Metadata, Viewport } from 'next';
import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Site } from '@/lib/types';
import { Header } from '@/components/header';
import { SessionProvider } from '@/components/session-provider';
import './globals.css';
export const metadata: Metadata = {
  title: { default: '摄影协会 · 在日常里，看见', template: '%s · 摄影协会' },
  description: '摄影协会的作品、活动与影像档案。',
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#f8f9f8' };
export const dynamic = 'force-dynamic';
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const site = await serverApi<Site>('site/');
  return (
    <html lang="zh-CN" data-scroll-behavior="smooth">
      <body>
        <a className="skip-link" href="#main">
          跳到主要内容
        </a>
        <SessionProvider>
          <Header site={site} />
          <main id="main">{children}</main>
          <footer className="site-footer">
            <div>
              <Link className="footer-brand" href="/">
                {site.name}
              </Link>
              <p>把此刻留下，让影像继续发生。</p>
            </div>
            <nav aria-label="页脚导航">
              <Link href="/works">作品馆</Link>
              <Link href="/archive">资料归档</Link>
              <Link href="/about#join">加入我们</Link>
              <Link href="/privacy">隐私与作品使用</Link>
            </nav>
            <div className="footer-bottom">
              <span>
                © {new Date().getFullYear()} {site.name}
              </span>
              <span>
                {[site.has_demo ? '示例作品待替换' : '', !site.logo_url ? 'Logo 设计中' : '']
                  .filter(Boolean)
                  .join(' / ')}
              </span>
            </div>
          </footer>
        </SessionProvider>
      </body>
    </html>
  );
}
