import Link from 'next/link';
import type { ClubEvent, Collection, Page } from '@/lib/types';
import { serverApi } from '@/lib/server-api';
import { Gallery } from '@/components/gallery';
import { date } from '@/lib/format';
import { CopyLink } from '@/components/motion';
export default async function Activity({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [event, collections] = await Promise.all([
    serverApi<ClubEvent>(`events/${id}/`, { anonymous: true }),
    serverApi<Page<Collection>>(`collections/?event=${id}&placeholder=0`, { anonymous: true }),
  ]);
  const photos = [...(event.photos || []), ...collections.results.flatMap((c) => c.photos)];
  return (
    <article className="gl-page gl-album-detail">
      <Link className="gl-back" href="/activities">
        活动 / Together
      </Link>
      <header className="gl-page-heading">
        <h1>{event.title}</h1>
      </header>
      <div className="gl-event-meta">
        <time dateTime={event.starts_at}>
          {date(event.starts_at, { year: 'numeric', month: 'long', day: 'numeric' })}
        </time>
        <span>{event.location}</span>
      </div>
      <p className="gl-album-description">{event.description}</p>
      {photos.length ? (
        <Gallery photos={photos} />
      ) : (
        <div className="gl-awaiting-photos">
          <span>Photographs to follow</span>
          <p>这场活动的照片还没有整理上来。</p>
        </div>
      )}
      <div className="gl-detail-end">
        <Link href="/activities">全部活动</Link>
        <CopyLink />
      </div>
    </article>
  );
}
