import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { ClubEvent, Page } from '@/lib/types';
import { EventCards } from '../event-cards';
export const metadata = { title: '活动' };
export default async function Activities({
  searchParams,
}: {
  searchParams: Promise<{ eventsPage?: string; q?: string }>;
}) {
  const query = await searchParams;
  const q = (query.q || '').trim();
  const eventsPage = Math.max(1, Math.trunc(Number(query.eventsPage) || 1));
  const [past, upcoming] = await Promise.all([
    serverApi<Page<ClubEvent>>(`events/?when=past&page=${eventsPage}&q=${encodeURIComponent(q)}`, {
      anonymous: true,
    }),
    serverApi<Page<ClubEvent>>('events/?when=upcoming', { anonymous: true }),
  ]);
  const url = (event: number) => `?${new URLSearchParams({ eventsPage: String(event), q })}`;
  return (
    <div className="gl-page">
      <header className="gl-page-heading">
        <p>Activities</p>
        <h1>活动记录</h1>
      </header>
      {upcoming.results.length > 0 && (
        <section className="wall-next-event">
          <h2>接下来</h2>
          <EventCards events={upcoming.results} expanded />
        </section>
      )}
      <section className="wall-events-first" aria-label="活动记录">
        <form className="gl-event-search" action="/activities">
          <label htmlFor="event-search">回看一次活动</label>
          <div>
            <input
              id="event-search"
              name="q"
              defaultValue={q}
              placeholder="输入活动名称或地点"
              type="search"
            />
            <button type="submit">查找</button>
          </div>
        </form>
        <EventCards events={past.results} expanded />
        {!past.count && <p className="wall-empty">没有找到相关活动。</p>}
        {(past.previous || past.next) && (
          <nav className="ex-pagination" aria-label="活动记录翻页">
            {past.previous ? <Link href={url(eventsPage - 1)}>较新活动</Link> : <span />}
            <span>活动记录</span>
            {past.next ? <Link href={url(eventsPage + 1)}>较早活动</Link> : <span />}
          </nav>
        )}
      </section>
    </div>
  );
}
