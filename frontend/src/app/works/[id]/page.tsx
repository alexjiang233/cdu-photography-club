import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Collection } from '@/lib/types';
import { DemoBadge } from '@/components/ui';
import { Gallery } from '@/components/gallery';
import { DiscussionPanel } from '@/components/discussion';
import { date, statusLabel } from '@/lib/format';
export default async function WorkDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const work = await serverApi<Collection>(`collections/${id}/`);
  return (
    <div className="container">
      <nav className="breadcrumbs" aria-label="当前位置">
        <Link href="/works">作品馆</Link>
        <span>/</span>
        <span>{work.title}</span>
      </nav>
      <header className="detail-header">
        {work.is_demo && <DemoBadge />}
        <h1>{work.title}</h1>
        <div className="detail-meta">
          {work.author.is_public ? (
            <Link href={`/members/${work.author.id}`}>摄影 / {work.author.display_name}</Link>
          ) : (
            <span>摄影 / {work.author.display_name}</span>
          )}
          <span>{work.photos.length} 张照片</span>
          {work.published_at && <span>{date(work.published_at)}</span>}
          {work.status !== 'published' && <span>{statusLabel[work.status]}</span>}
        </div>
      </header>
      {work.editable && (
        <div className="status-line">
          <Link className="button secondary" href={`/dashboard/submit?id=${id}`}>
            管理这组作品
          </Link>
          {work.review_note && <p className="form-message">审核意见：{work.review_note}</p>}
        </div>
      )}
      <p className="prose detail-description">{work.description}</p>
      <Gallery photos={work.photos} />
      {work.event && (
        <p className="prose">
          <Link className="text-link" href={`/events/${work.event}`}>
            查看关联活动
          </Link>
        </p>
      )}
      <DiscussionPanel resource="collections" id={id} />
    </div>
  );
}
