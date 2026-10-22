import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Collection } from '@/lib/types';
import { serverApi } from '@/lib/server-api';
import { Gallery } from '@/components/gallery';
import { CopyLink } from '@/components/motion';
export default async function Album({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ photo?: string }>;
}) {
  const { id } = await params;
  const work = await serverApi<Collection>(`collections/${id}/`, { anonymous: true });
  if (work.is_demo || work.is_placeholder) notFound();
  const selected = (await searchParams).photo;
  const initialIndex = Math.max(
    0,
    work.photos.findIndex((photo) => photo.id === selected),
  );
  return (
    <article className="gl-page gl-album-detail">
      <Link className="gl-back" href="/works">
        照片 / Photographs
      </Link>
      <header className="gl-page-heading">
        <h1>{work.title}</h1>
        <span>{work.photos.length} photographs</span>
      </header>
      <p className="gl-album-description">{work.description}</p>
      <Gallery key={initialIndex} photos={work.photos} initialIndex={initialIndex} />
      <div className="gl-detail-end">
        <Link href="/activities">看看活动</Link>
        <CopyLink />
      </div>
    </article>
  );
}
