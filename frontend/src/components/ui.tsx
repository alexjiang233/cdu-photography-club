import Link from 'next/link';
import { ArrowUpRight, Camera, FileText } from 'lucide-react';
import type { ArchiveDocument, ClubEvent, Collection, Page } from '@/lib/types';
import { categories, date } from '@/lib/format';

export function PageHeading({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {children}
    </div>
  );
}
export function DemoBadge() {
  return <span className="badge">示例内容</span>;
}
export function Empty({
  title = '这里还没有内容',
  description = '新的记录发布后，会出现在这里。',
  children,
}: {
  title?: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      <Camera size={30} strokeWidth={1} aria-hidden="true" />
      <h2>{title}</h2>
      <p>{description}</p>
      {children}
    </div>
  );
}
export function WorkCard({ work, priority = false }: { work: Collection; priority?: boolean }) {
  const photo = work.photos[0];
  return (
    <article className="work-card">
      <Link href={`/works/${work.id}`} className="work-image">
        {photo?.thumbnail_url ? (
          <img
            src={photo.thumbnail_url}
            alt={photo.caption}
            width={photo.width || 1000}
            height={photo.height || 750}
            loading={priority ? 'eager' : 'lazy'}
            fetchPriority={priority ? 'high' : 'auto'}
          />
        ) : (
          <div className="image-placeholder">
            <Camera aria-hidden="true" />
          </div>
        )}
      </Link>
      <div className="work-caption">
        <div>
          <h3>
            <Link href={`/works/${work.id}`}>{work.title}</Link>
          </h3>
          <p>
            {work.author.display_name}
            {work.tags.length > 0 && ` / ${work.tags.join('、')}`}
          </p>
        </div>
        {work.is_demo ? <DemoBadge /> : <span className="muted">{work.photos.length} 张</span>}
      </div>
    </article>
  );
}
export function EventRow({ event }: { event: ClubEvent }) {
  const expired = new Date(event.registration_deadline) < new Date();
  const state = event.is_demo
    ? '示例活动'
    : event.registration_open && !expired
      ? '开放报名'
      : '活动记录';
  return (
    <Link href={`/events/${event.id}`} className="event-row">
      <time dateTime={event.starts_at}>
        <strong>{date(event.starts_at, { day: '2-digit' })}</strong>
        <span>{date(event.starts_at, { year: 'numeric', month: 'short' })}</span>
      </time>
      <div className="event-row-info">
        <h3>{event.title}</h3>
        <p>{event.location}</p>
      </div>
      <span className="event-state">{state}</span>
      <ArrowUpRight size={23} strokeWidth={1.3} aria-hidden="true" />
    </Link>
  );
}
export function DocumentRow({ document }: { document: ArchiveDocument }) {
  return (
    <Link className="document-row" href={`/archive/${document.id}`}>
      <FileText size={23} strokeWidth={1.3} aria-hidden="true" />
      <div>
        <h3>{document.title}</h3>
        <p>
          {document.year} / {categories[document.category] || document.category} /{' '}
          {document.visibility === 'public' ? '公开资料' : '内部资料'}
        </p>
      </div>
      {document.is_demo && <DemoBadge />}
      <ArrowUpRight size={20} aria-hidden="true" />
    </Link>
  );
}
export function Pagination({
  page,
  data,
  params,
}: {
  page: number;
  data: Page<unknown>;
  params: Record<string, string>;
}) {
  const link = (value: number) => `?${new URLSearchParams({ ...params, page: String(value) })}`;
  if (!data.next && !data.previous) return null;
  return (
    <nav className="pagination" aria-label="分页">
      {data.previous ? (
        <Link className="button secondary" href={link(page - 1)}>
          上一页
        </Link>
      ) : (
        <span />
      )}
      <span>
        第 {page} 页 / 共 {data.count} 条
      </span>
      {data.next ? (
        <Link className="button secondary" href={link(page + 1)}>
          下一页
        </Link>
      ) : (
        <span />
      )}
    </nav>
  );
}
