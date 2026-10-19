'use client';
import { useSearchParams } from 'next/navigation';
import { DocumentRow, Empty, EventRow, PageHeading, WorkCard } from '@/components/ui';
import { categories } from '@/lib/format';
import type { ArchiveDocument, ClubEvent, Collection, Page } from '@/lib/types';
import { demo, readPreview } from './data';

export function PreviewListing({ kind }: { kind: 'works' | 'events' | 'archive' | 'search' }) {
  const query = useSearchParams();
  const q = query.get('q') || '';
  const params = new URLSearchParams(query.toString());
  const works = readPreview(`collections/?${params}`) as Page<Collection>;
  const events = readPreview(`events/?${params}`) as Page<ClubEvent>;
  const docs = readPreview(`documents/?${params}`) as Page<ArchiveDocument>;
  const title = { works: '作品馆', events: '一起拍，也一起看', archive: '经验与记录，都在这里', search: '找到一份记录' }[kind];
  const matches = kind === 'search' ? works.count + events.count + docs.count : kind === 'works' ? works.count : kind === 'events' ? events.count : docs.count;
  return <div className="container">
    <PageHeading title={title} description="当前为静态预览，可搜索公开示例内容。" />
    <form className="filters" action={`${process.env.NEXT_PUBLIC_BASE_PATH}/${kind}/`}>
      <div className="field search-field"><label htmlFor="preview-query">搜索关键词</label><input id="preview-query" name="q" defaultValue={q} placeholder="标题、简介或标签…" /></div>
      {kind === 'works' && <div className="field"><label htmlFor="preview-tag">主题</label><select id="preview-tag" name="tag" defaultValue={query.get('tag') || ''}><option value="">全部主题</option>{demo.site.tags.map(tag => <option key={tag}>{tag}</option>)}</select></div>}
      {kind === 'works' && query.get('event') && <input type="hidden" name="event" value={query.get('event')!} />}
      {kind === 'archive' && <><div className="field"><label htmlFor="preview-year">年份</label><input id="preview-year" name="year" type="number" defaultValue={query.get('year') || ''} /></div><div className="field"><label htmlFor="preview-category">类别</label><select id="preview-category" name="category" defaultValue={query.get('category') || ''}><option value="">全部类别</option>{Object.entries(categories).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></>}
      <button className="button">查找</button>
    </form>
    <p className="search-count" aria-live="polite">找到 {matches} 条示例记录</p>
    {(kind === 'works' || kind === 'search') && <section>{kind === 'search' && <h2 className="section-title">作品</h2>}<div className="work-grid">{works.results.map(work => <WorkCard key={work.id} work={work} />)}</div></section>}
    {(kind === 'events' || kind === 'search') && <section>{kind === 'search' && <h2 className="section-title">活动</h2>}{events.results.map(event => <EventRow key={event.id} event={event} />)}</section>}
    {(kind === 'archive' || kind === 'search') && <section>{kind === 'search' && <h2 className="section-title">资料</h2>}{docs.results.map(document => <DocumentRow key={document.id} document={document} />)}</section>}
    {!matches && <Empty title="没有找到对应记录" description="请尝试其他关键词或清除筛选条件。" />}
  </div>;
}
