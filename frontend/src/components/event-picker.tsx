'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/client-api';
import type { ClubEvent, Page } from '@/lib/types';

export function EventPicker({
  initialValue = '',
  disabled = false,
}: {
  initialValue?: string | null;
  disabled?: boolean;
}) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(initialValue || '');
  const [events, setEvents] = useState<ClubEvent[]>([]);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(async () => {
      try {
        const data = await api<Page<ClubEvent>>(`events/?q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
        });
        const options = data.results;
        if (selected && !options.some((event) => event.id === selected))
          options.unshift(
            await api<ClubEvent>(`events/${selected}/`, { signal: controller.signal }),
          );
        setEvents(options);
        setError('');
      } catch (err) {
        if (!controller.signal.aborted) setError((err as Error).message);
      }
    }, 200);
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [query, selected]);
  return (
    <div className="field">
      <label htmlFor="event-search">查找要关联的活动</label>
      <input
        id="event-search"
        value={query}
        onChange={(event) => {
          event.stopPropagation();
          setQuery(event.target.value);
        }}
        disabled={disabled}
        placeholder="输入活动名称，查找往期记录…"
        autoComplete="off"
      />
      <label htmlFor="work-event">关联活动（可选）</label>
      <select
        id="work-event"
        name="event"
        value={selected}
        onChange={(event) => setSelected(event.target.value)}
        disabled={disabled}
      >
        <option value="">独立创作</option>
        {events.map((event) => (
          <option value={event.id} key={event.id}>
            {event.title}
          </option>
        ))}
      </select>
      {error && (
        <p className="form-message error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
