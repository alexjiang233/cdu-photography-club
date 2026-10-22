'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
const items = [
  ['/works', '照片', 'Photographs'],
  ['/activities', '活动', 'Activities'],
  ['/about', '关于', 'About'],
];
export function GalleryHeader({ logo }: { logo: string | null }) {
  const path = usePathname();
  const home = path === '/';
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 32);
    update();
    window.addEventListener('scroll', update, { passive: true });
    return () => window.removeEventListener('scroll', update);
  }, []);
  const overlay = home && !scrolled;
  return (
    <>
      <div className={`gl-header-shell${overlay ? ' gl-header-over-cover' : ''}`}>
        <header className={`ex-header${overlay ? ' ex-header-cover' : ''}`}>
          <Link className="ex-brand" href="/#gallery-top" aria-label="成都大学摄影协会首页">
            <img
              className="gl-logo"
              src={overlay ? '/association/logo-light.svg' : logo || '/association/logo.svg'}
              width="42"
              height="42"
              alt=""
            />
            <span className="gl-header-wordmark" aria-hidden="true">
              <span className="gl-header-wordmark-university" />
              <span className="gl-header-wordmark-society" />
            </span>
          </Link>
          <nav className="ex-nav" aria-label="主导航">
            {items.map(([href, title, english]) => (
              <Link
                href={href}
                key={href}
                aria-current={path.startsWith(href) ? 'page' : undefined}
              >
                <span>{title}</span>
                <small>{english}</small>
              </Link>
            ))}
          </nav>
        </header>
      </div>
      {!home && <div className="gl-header-spacer" aria-hidden="true" />}
    </>
  );
}
