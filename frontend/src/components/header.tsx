'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Aperture, ArrowUpRight, Menu, Search, X } from 'lucide-react';
import { useSession } from './session-provider';
import type { Site } from '@/lib/types';
const links = [
  ['/works', '作品'],
  ['/events', '活动'],
  ['/archive', '资料'],
  ['/about', '关于我们'],
];
export function Header({ site }: { site: Site }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const { user } = useSession();
  return (
    <header className="site-header">
      <Link
        className="brand"
        href="/"
        aria-label={`${site.name}首页`}
        onClick={() => setOpen(false)}
      >
        {site.logo_url ? (
          <img src={site.logo_url} width="40" height="40" alt="" />
        ) : (
          <Aperture size={34} strokeWidth={1.35} aria-hidden="true" />
        )}
        <span>
          {site.name}
          <small>Photography Association</small>
        </span>
      </Link>
      <nav className="desktop-nav" aria-label="主导航">
        {links.map(([href, label]) => (
          <Link key={href} href={href} aria-current={path.startsWith(href) ? 'page' : undefined}>
            {label}
          </Link>
        ))}
      </nav>
      <div className="header-actions">
        <Link className="icon-button" href="/search" aria-label="搜索作品、活动和资料">
          <Search size={20} aria-hidden="true" />
        </Link>
        <Link className="member-link" href={user.authenticated ? '/dashboard' : '/login'}>
          {user.authenticated ? '成员中心' : '成员登录'}
          <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
        <button
          className="icon-button mobile-toggle"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? '关闭导航' : '打开导航'}
        >
          {open ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
      </div>
      {open && (
        <nav className="mobile-nav" id="mobile-nav" aria-label="手机导航">
          {links.map(([href, label]) => (
            <Link href={href} key={href} onClick={() => setOpen(false)}>
              {label}
            </Link>
          ))}
          <Link href="/dashboard" onClick={() => setOpen(false)}>
            成员中心
          </Link>
        </nav>
      )}
    </header>
  );
}
