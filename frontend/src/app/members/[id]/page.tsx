import Link from 'next/link';
import { serverApi } from '@/lib/server-api';
import type { Collection, Page, Profile } from '@/lib/types';
import { DemoBadge, Empty, PageHeading, Pagination, WorkCard } from '@/components/ui';
export default async function Member({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const page = Math.max(1, Number(query.page) || 1);
  const [member, works] = await Promise.all([
    serverApi<Profile>(`members/${id}/`),
    serverApi<Page<Collection>>(`collections/?author=${id}&page=${page}`),
  ]);
  return (
    <div className="container">
      <nav className="breadcrumbs">
        <Link href="/about">关于我们</Link>
        <span>/</span>
        <span>作者主页</span>
      </nav>
      <PageHeading title={member.display_name} description={member.bio}>
        {member.is_demo && <DemoBadge />}
      </PageHeading>
      {member.cohort && <p className="muted">{member.cohort}</p>}
      <h2 className="section-title">作品系列</h2>
      {works.results.length ? (
        <div className="work-grid">
          {works.results.map((work) => (
            <WorkCard work={work} key={work.id} />
          ))}
        </div>
      ) : (
        <Empty title="作品正在准备中" />
      )}
      <Pagination page={page} data={works} params={{}} />
    </div>
  );
}
