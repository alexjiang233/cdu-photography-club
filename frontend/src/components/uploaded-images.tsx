'use client';

import { useState } from 'react';
import { api, post } from '@/lib/client-api';
import type { Asset, Page } from '@/lib/types';

export function UploadedImages({
  collectionId,
  disabled,
  onAdded,
}: {
  collectionId: string;
  disabled: boolean;
  onAdded: () => Promise<void>;
}) {
  const [data, setData] = useState<Page<Asset> | null>(null);
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function load(next = 1) {
    setBusy(true);
    setError('');
    try {
      setData(await api<Page<Asset>>(`upload/?collection=${collectionId}&page=${next}`));
      setPage(next);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function add(asset: Asset) {
    setBusy(true);
    setError('');
    try {
      await post(`collections/${collectionId}/photos/`, {
        asset_id: asset.id,
        caption: asset.original_name.replace(/\.[^.]+$/, ''),
      });
      await onAdded();
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details
      className="existing-uploads"
      onToggle={(event) => {
        if (event.currentTarget.open && !data) load();
      }}
    >
      <summary>从已上传图片中添加</summary>
      <p className="muted">上传处理中断或刷新页面后，可在这里找回图片。处理中时请稍后刷新。</p>
      <button
        className="button secondary"
        type="button"
        onClick={() => load(page)}
        disabled={busy || disabled}
      >
        刷新图片列表
      </button>
      {error && (
        <p className="form-message error" role="alert">
          {error}
        </p>
      )}
      <div className="existing-upload-grid">
        {data?.results.map((asset) => (
          <div key={asset.id}>
            {asset.thumbnail_url && (
              <img
                src={asset.thumbnail_url}
                alt={asset.original_name}
                width={200}
                height={150}
                loading="lazy"
              />
            )}
            <p>{asset.original_name}</p>
            {asset.state === 'ready' ? (
              <button
                className="button secondary"
                disabled={busy || disabled}
                onClick={() => add(asset)}
              >
                添加到作品
              </button>
            ) : (
              <p className="muted">
                {asset.state === 'processing'
                  ? '正在处理…'
                  : asset.error || '处理失败，请重新导出后上传。'}
              </p>
            )}
          </div>
        ))}
      </div>
      {data && !data.count && <p className="muted">没有其他已上传的图片。</p>}
      <div className="form-actions">
        {data?.previous && (
          <button className="button secondary" disabled={busy} onClick={() => load(page - 1)}>
            上一页
          </button>
        )}
        {data?.next && (
          <button className="button secondary" disabled={busy} onClick={() => load(page + 1)}>
            下一页
          </button>
        )}
      </div>
    </details>
  );
}
