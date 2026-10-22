'use client';
import { usePathname } from 'next/navigation';
export default function GalleryTemplate({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return <div className={path === '/' ? undefined : 'gl-content-enter'}>{children}</div>;
}
