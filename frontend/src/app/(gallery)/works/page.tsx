import Link from 'next/link';
import type { Collection, Page } from '@/lib/types';
import { serverApi } from '@/lib/server-api';
import { PhotoBrowser } from '../photo-browser';
export const metadata = { title: '照片' };
export default async function Photographs({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const page = Math.max(1, Math.trunc(Number((await searchParams).page) || 1));
  const data = await serverApi<Page<Collection>>(`collections/?placeholder=0&page=${page}`, {
    anonymous: true,
  });
  return (
    <div className="gl-page gl-browse-page">
      <header className="gl-page-heading">
        <p>Photographs</p>
        <h1>照片</h1>
      </header>
      <PhotoBrowser albums={data.results} />
      <nav className="ex-pagination" aria-label="照片翻页">
        {data.previous ? <Link href={`?page=${page - 1}`}>上一页相册</Link> : <span />}
        <span>
          第 {page} 页 · 共 {data.count} 组相册
        </span>
        {data.next ? <Link href={`?page=${page + 1}`}>下一页相册</Link> : <span />}
      </nav>
    </div>
  );
}
