import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Collection, Page, ClubEvent } from '@/lib/types';
import { AlbumCard } from './album-card';
import { PhotoWall } from './photo-wall';
import { EventCards } from './event-cards';
export const metadata = {
  title: '摄影、活动与日常',
  description: '成都大学摄影协会的照片、活动与拍摄记录。',
};
export default async function GalleryHome() {
  const [works, events, upcoming] = await Promise.all([
    serverApi<Page<Collection>>('collections/?placeholder=0', { anonymous: true }),
    serverApi<Page<ClubEvent>>('events/?when=past', { anonymous: true }),
    serverApi<Page<ClubEvent>>('events/?when=upcoming', { anonymous: true }),
  ]);
  return (
    <>
      <section className="wall-hero" id="gallery-top" aria-labelledby="wall-title">
        <PhotoWall />
        <div className="wall-scrim" aria-hidden="true" />
        <div className="wall-hero-copy">
          <p className="wall-hero-english">Photography Society, CDU</p>
          <h1 id="wall-title">
            <span className="gl-cover-line">
              <span>摄录人间万象</span>
            </span>
            <span className="gl-cover-line">
              <span>聚焦永恒瞬间</span>
            </span>
          </h1>
        </div>
        <div className="wall-hero-foot">
          <a href="#photographs">
            向下看照片 <span aria-hidden="true">↓</span>
          </a>
          <span>封面为视觉样片</span>
        </div>
      </section>
      <div className="gl-home">
        <section className="gl-section" id="photographs">
          <header className="gl-section-heading" data-reveal="gallery-heading" data-scroll-reveal>
            <span className="wall-section-label">Photographs</span>
            <h2>照片</h2>
            <Link href="/works">全部照片 ↗</Link>
          </header>
          <div className="gl-album-grid">
            {works.results.slice(0, 4).map((album) => (
              <AlbumCard album={album} key={album.id} />
            ))}
          </div>
        </section>
        <section className="gl-section">
          <header className="gl-section-heading" data-reveal="gallery-heading" data-scroll-reveal>
            <span className="wall-section-label">Activities</span>
            <h2>活动</h2>
            <Link href="/activities">活动记录 ↗</Link>
          </header>
          {upcoming.results[0] && (
            <div className="wall-next-event">
              <span>接下来 / Next</span>
              <EventCards events={upcoming.results.slice(0, 1)} />
            </div>
          )}
          <EventCards events={events.results.slice(0, 3)} />
        </section>
      </div>
    </>
  );
}
