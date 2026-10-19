import type { Metadata } from 'next';
import { serverApi } from '@/lib/server-api';
import type { ClubEvent, Page } from '@/lib/types';
import { Empty, EventRow, PageHeading, Pagination } from '@/components/ui';
export const metadata: Metadata = { title: '活动' };
export default async function Events({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const query = await searchParams;
  const page = Math.max(1, Number(query.page) || 1);
  const params = { q: query.q || '' };
  const data = await serverApi<Page<ClubEvent>>(
    `events/?${new URLSearchParams({ ...params, page: String(page) })}`,
  );
  return (
    <div className="container">
      <PageHeading
        title="一起拍，也一起看"
        description="外拍、分享、展览。每一次相聚，都留下新的记录。"
      />
      <form className="filters">
        <div className="field search-field">
          <label htmlFor="event-query">查找活动</label>
          <input
            id="event-query"
            name="q"
            defaultValue={params.q}
            placeholder="活动名称或介绍中的关键词…"
            autoComplete="off"
          />
        </div>
        <button className="button">查找活动</button>
      </form>
      {data.results.length ? (
        data.results.map((event) => <EventRow event={event} key={event.id} />)
      ) : (
        <Empty title="还没有对应的活动" />
      )}
      <Pagination page={page} data={data} params={params} />
    </div>
  );
}
