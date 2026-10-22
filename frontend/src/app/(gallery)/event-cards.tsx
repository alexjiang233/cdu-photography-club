import Link from 'next/link';
import type { ClubEvent } from '@/lib/types';
import { date } from '@/lib/format';

export function EventCards({
  events,
  expanded = false,
}: {
  events: ClubEvent[];
  expanded?: boolean;
}) {
  return (
    <div className={`gl-event-cards${expanded ? ' gl-event-cards-expanded' : ''}`}>
      {events.map((event) => (
        <Link
          key={event.id}
          href={`/activities/${event.id}`}
          className="gl-event-ticket"
          data-reveal="gallery-card"
          data-scroll-reveal
        >
          <time dateTime={event.starts_at}>
            <strong>{date(event.starts_at, { day: '2-digit' }).replace(/[^0-9]/g, '')}</strong>
            <span>
              {date(event.starts_at, { year: 'numeric', month: '2-digit' })
                .replace('年', '/')
                .replace('月', '')}
            </span>
          </time>
          <div>
            <span className="gl-ticket-location">{event.location}</span>
            <h3>{event.title}</h3>
            <p>{event.description}</p>
            <span className="gl-ticket-open">
              查看活动 <span aria-hidden="true">↗</span>
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
