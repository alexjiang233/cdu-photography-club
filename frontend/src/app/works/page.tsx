import type { Metadata } from 'next';
import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Collection, Page, Site } from '@/lib/types';
import { Empty, PageHeading, Pagination, WorkCard } from '@/components/ui';
export const metadata: Metadata = { title: '作品馆' };
export default async function Works({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const query = await searchParams;
  const page = Math.max(1, Number(query.page) || 1);
  const params = { q: query.q || '', tag: query.tag || '', event: query.event || '' };
  const [data, site] = await Promise.all([
    serverApi<Page<Collection>>(
      `collections/?${new URLSearchParams({ ...params, page: String(page) })}`,
    ),
    serverApi<Site>('site/'),
  ]);
  return (
    <div className="container">
      <PageHeading title="作品馆" description="从一组照片，走进另一个人的视角。" />
      <form className="filters" action="/works">
        {params.event && <input type="hidden" name="event" value={params.event} />}
        <div className="field search-field">
          <label htmlFor="work-query">查找作品</label>
          <input
            id="work-query"
            name="q"
            defaultValue={params.q}
            placeholder="作品名、主题或拍摄故事…"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label htmlFor="work-tag">主题</label>
          <select id="work-tag" name="tag" defaultValue={params.tag}>
            <option value="">全部主题</option>
            {site.tags.map((tag) => (
              <option key={tag}>{tag}</option>
            ))}
          </select>
        </div>
        <button className="button">筛选作品</button>
      </form>
      {params.event && (
        <p className="muted" style={{ marginBottom: 20 }}>
          正在查看关联活动的作品。
          <Link className="text-link" href="/works">
            清除活动筛选
          </Link>
        </p>
      )}
      {data.results.length ? (
        <div className="work-grid">
          {data.results.map((work, i) => (
            <WorkCard work={work} key={work.id} priority={i < 3} />
          ))}
        </div>
      ) : (
        <Empty
          title="没有找到对应的作品"
          description="可以换一个关键词，或者清除主题筛选后再看看。"
        />
      )}
      <Pagination page={page} data={data} params={params} />
    </div>
  );
}
