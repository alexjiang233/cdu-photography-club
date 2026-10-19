import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { ArchiveDocument, ClubEvent, Collection, Page } from '@/lib/types';
import { DocumentRow, Empty, EventRow, PageHeading, WorkCard } from '@/components/ui';
export default async function Search({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = '' } = await searchParams;
  const term = q.trim().slice(0, 100);
  const data = term
    ? await Promise.all([
        serverApi<Page<Collection>>(`collections/?q=${encodeURIComponent(term)}`),
        serverApi<Page<ClubEvent>>(`events/?q=${encodeURIComponent(term)}`),
        serverApi<Page<ArchiveDocument>>(`documents/?q=${encodeURIComponent(term)}`),
      ])
    : null;
  return (
    <div className="container">
      <PageHeading title="找到一份记录" description="搜索作品、活动与资料的标题、简介和标签。" />
      <form className="filters" action="/search">
        <div className="field search-field">
          <label htmlFor="site-search">搜索关键词</label>
          <input
            id="site-search"
            name="q"
            defaultValue={term}
            maxLength={100}
            placeholder="你想找什么…"
            autoComplete="off"
          />
        </div>
        <button className="button">搜索</button>
      </form>
      {!data ? (
        <Empty title="从一个关键词开始" description="例如：校园、外拍、摄影基础。" />
      ) : data.every((group) => !group.count) ? (
        <Empty title="没有找到对应记录" description="可以换一个关键词，或登录后搜索内部资料。" />
      ) : (
        <>
          <section className="search-result-group">
            <h2 className="section-title">作品 / {data[0].count}</h2>
            <div className="work-grid">
              {data[0].results.slice(0, 6).map((work) => (
                <WorkCard key={work.id} work={work} />
              ))}
            </div>
            {data[0].count > 6 && (
              <Link className="text-link" href={`/works?q=${encodeURIComponent(term)}`}>
                查看全部匹配作品
              </Link>
            )}
          </section>
          <section className="search-result-group">
            <h2 className="section-title">活动 / {data[1].count}</h2>
            {data[1].results.slice(0, 5).map((event) => (
              <EventRow event={event} key={event.id} />
            ))}
            {data[1].count > 5 && (
              <Link className="text-link" href={`/events?q=${encodeURIComponent(term)}`}>
                查看全部匹配活动
              </Link>
            )}
          </section>
          <section>
            <h2 className="section-title">资料 / {data[2].count}</h2>
            {data[2].results.slice(0, 5).map((doc) => (
              <DocumentRow document={doc} key={doc.id} />
            ))}
            {data[2].count > 5 && (
              <Link className="text-link" href={`/archive?q=${encodeURIComponent(term)}`}>
                查看全部匹配资料
              </Link>
            )}
          </section>
        </>
      )}
    </div>
  );
}
