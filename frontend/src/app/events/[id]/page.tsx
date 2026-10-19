import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { ArchiveDocument, ClubEvent, Collection, Page } from '@/lib/types';
import { DemoBadge, DocumentRow, WorkCard } from '@/components/ui';
import { RegistrationForm } from '@/components/registration-form';
import { DiscussionPanel } from '@/components/discussion';
import { date } from '@/lib/format';
export default async function EventDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [event, works, docs] = await Promise.all([
    serverApi<ClubEvent>(`events/${id}/`),
    serverApi<Page<Collection>>(`collections/?event=${id}`),
    serverApi<Page<ArchiveDocument>>(`documents/?event=${id}`),
  ]);
  return (
    <div className="container">
      <nav className="breadcrumbs" aria-label="当前位置">
        <Link href="/events">活动</Link>
        <span>/</span>
        <span>{event.title}</span>
      </nav>
      <header className="detail-header">
        {event.is_demo && <DemoBadge />}
        <h1>{event.title}</h1>
        <p className="muted">{event.location}</p>
      </header>
      <div className="content-grid">
        <div>
          {event.cover_url && (
            <img
              className="cover-image"
              src={event.cover_url}
              alt={`${event.title}的活动图片`}
              width="1200"
              height="800"
            />
          )}
          <p className="prose">{event.description}</p>
          {event.editable && (
            <Link className="text-link" href={`/admin/club/event/${id}/change/`}>
              管理活动内容与报名
            </Link>
          )}
        </div>
        <aside className="info-panel">
          <h2>活动信息</h2>
          <dl className="info-list">
            <div>
              <dt>活动时间</dt>
              <dd>
                {date(event.starts_at, {
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
                <br />至{' '}
                {date(event.ends_at, {
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </dd>
            </div>
            <div>
              <dt>报名截止</dt>
              <dd>
                {date(event.registration_deadline, {
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </dd>
            </div>
            <div>
              <dt>参加人数</dt>
              <dd>
                {event.registration_count} / {event.capacity} 人
              </dd>
            </div>
          </dl>
          <RegistrationForm event={event} />
        </aside>
      </div>
      {works.results.length > 0 && (
        <section className="section">
          <h2 className="section-title">这次活动留下的作品</h2>
          <div className="work-grid">
            {works.results.slice(0, 6).map((work) => (
              <WorkCard work={work} key={work.id} />
            ))}
          </div>
          {works.next && (
            <Link className="text-link" href={`/works?event=${id}`}>
              查看全部关联作品
            </Link>
          )}
        </section>
      )}
      {docs.results.length > 0 && (
        <section className="section">
          <h2 className="section-title">相关资料</h2>
          {docs.results.map((doc) => (
            <DocumentRow document={doc} key={doc.id} />
          ))}
        </section>
      )}
      <DiscussionPanel resource="events" id={id} />
    </div>
  );
}
