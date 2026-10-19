import Link from 'next/link';
import { Download } from 'lucide-react';
import { serverApi } from '@/lib/server-api';
import type { ArchiveDocument } from '@/lib/types';
import { DemoBadge, Empty } from '@/components/ui';
import { categories, date, size } from '@/lib/format';
export default async function DocumentDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const doc = await serverApi<ArchiveDocument>(`documents/${id}/`);
  return (
    <div className="container">
      <nav className="breadcrumbs" aria-label="当前位置">
        <Link href="/archive">资料归档</Link>
        <span>/</span>
        <span>{doc.title}</span>
      </nav>
      <header className="detail-header">
        {doc.is_demo && <DemoBadge />}
        <h1>{doc.title}</h1>
        <div className="detail-meta">
          <span>{doc.year}</span>
          <span>{categories[doc.category]}</span>
          <span>{doc.visibility === 'public' ? '公开资料' : '授权资料'}</span>
        </div>
      </header>
      <p className="prose detail-description">{doc.description}</p>
      <div className="editor-shell">
        <h2 className="section-title">文件与历史版本</h2>
        {doc.versions.length ? (
          doc.versions.map((version) => (
            <article key={version.id} className="document-version">
              <div>
                <h3>{version.filename}</h3>
                <p>
                  版本 {version.version} / {size(version.size)} / {date(version.created_at)}
                </p>
                <p>{version.note}</p>
              </div>
              <a className="button secondary" href={version.download_url} download>
                <Download size={17} aria-hidden="true" />
                下载文件
              </a>
            </article>
          ))
        ) : (
          <Empty title="文件尚未上传" />
        )}
        {doc.event && (
          <Link className="text-link" href={`/events/${doc.event}`}>
            查看关联活动
          </Link>
        )}
        {doc.editable && (
          <Link className="text-link" href={`/admin/club/document/${doc.id}/change/`}>
            管理文件版本
          </Link>
        )}
      </div>
    </div>
  );
}
