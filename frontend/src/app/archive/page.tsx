import type { Metadata } from 'next';
import { serverApi } from '@/lib/server-api';
import type { ArchiveDocument, Page } from '@/lib/types';
import { DocumentRow, Empty, PageHeading, Pagination } from '@/components/ui';
import { categories } from '@/lib/format';
export const metadata: Metadata = { title: '资料与归档' };
export default async function Archive({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const query = await searchParams;
  const page = Math.max(1, Number(query.page) || 1);
  const params = { q: query.q || '', year: query.year || '', category: query.category || '' };
  const data = await serverApi<Page<ArchiveDocument>>(
    `documents/?${new URLSearchParams({ ...params, page: String(page) })}`,
  );
  return (
    <div className="container">
      <PageHeading
        title="经验与记录，都在这里"
        description="按年份和类别查找教程、刊物与历史文件。登录后可查看获授权的内部资料。"
      />
      <form className="filters">
        <div className="field search-field">
          <label htmlFor="archive-query">资料关键词</label>
          <input
            id="archive-query"
            name="q"
            defaultValue={params.q}
            placeholder="标题、简介或标签…"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label htmlFor="archive-year">年份</label>
          <input
            id="archive-year"
            name="year"
            type="number"
            min="1900"
            max="2200"
            defaultValue={params.year}
            placeholder="例如 2026…"
          />
        </div>
        <div className="field">
          <label htmlFor="archive-category">类别</label>
          <select id="archive-category" name="category" defaultValue={params.category}>
            <option value="">全部类别</option>
            {Object.entries(categories).map(([value, name]) => (
              <option key={value} value={value}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <button className="button">查找资料</button>
      </form>
      <p className="search-count">找到 {data.count} 份可访问的资料</p>
      {data.results.length ? (
        data.results.map((doc) => <DocumentRow document={doc} key={doc.id} />)
      ) : (
        <Empty
          title="没有找到可访问的资料"
          description="试试其他关键词；内部资料需要成员登录后查看。"
        />
      )}
      <Pagination page={page} data={data} params={params} />
    </div>
  );
}
