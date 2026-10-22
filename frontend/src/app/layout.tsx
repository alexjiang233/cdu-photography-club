import type { Metadata, Viewport } from 'next';
import { MotionRoot } from '@/components/motion';
import './globals.css';
import './motion.css';
export const metadata: Metadata = {
  title: { default: '成都大学摄影协会', template: '%s · 摄影协会' },
  description: '成都大学摄影协会的照片、活动与日常。',
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    siteName: '成都大学摄影协会',
    title: '成都大学摄影协会',
    description: '成都大学摄影协会的照片、活动与日常。',
  },
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#f4f1e9' };
export const dynamic = 'force-dynamic';
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" data-scroll-behavior="smooth">
      <body>
        <MotionRoot />
        <main id="main">{children}</main>
      </body>
    </html>
  );
}
