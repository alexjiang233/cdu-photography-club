'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api, post } from '@/lib/client-api';
import type { Asset, Collection, Photo, Site } from '@/lib/types';
import { statusLabel } from '@/lib/format';
import { useSession } from './session-provider';
import { PageHeading } from './ui';
import { EventPicker } from './event-picker';
import { UploadedImages } from './uploaded-images';

async function upload(file: File): Promise<Asset> {
  const data = new FormData();
  data.append('file', file);
  let asset = await api<Asset>('upload/', { method: 'POST', body: data });
  for (let i = 0; asset.state === 'processing' && i < 45; i++) {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    asset = await api<Asset>(`assets/${asset.id}/`);
  }
  if (asset.state !== 'ready')
    throw new Error(asset.error || '图片仍在处理，稍后可从“已上传图片”中添加，无需重复上传。');
  return asset;
}
export function WorkEditor() {
  const { user, loading } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const id = params.get('id');
  const [work, setWork] = useState<Collection | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(!id);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const photoInput = useRef<HTMLInputElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const editable = !work || ['draft', 'returned'].includes(work.status);
  useEffect(() => {
    if (!loading && !user.authenticated) router.replace('/login?next=/dashboard/submit');
  }, [loading, user.authenticated]);
  useEffect(() => {
    if (!user.authenticated) return;
    api<Site>('site/')
      .then((site) => {
        setTags(site.tags);
      })
      .catch((err) => setError(err.message));
    if (id) {
      api<Collection>(`collections/${id}/`)
        .then((data) => {
          if (!data.editable) throw new Error('你没有修改该作品的权限。');
          setWork(data);
          setReady(true);
        })
        .catch((err) => setError(err.message));
    }
  }, [id, user.authenticated]);
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setMessage('');
    const data = new FormData(e.currentTarget);
    const payload = {
      title: data.get('title'),
      description: data.get('description'),
      visibility: data.get('visibility'),
      event: data.get('event') || null,
      tags: data.getAll('tags'),
    };
    try {
      const result = await api<Collection>(work ? `collections/${work.id}/` : 'collections/', {
        method: work ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      });
      setWork(result);
      setDirty(false);
      setMessage('草稿已保存，可以继续添加照片。');
      if (!id) router.replace(`/dashboard/submit?id=${result.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function addPhotos(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (!work || !files.length) return;
    setBusy(true);
    setError('');
    try {
      let order = work.photos.length;
      for (const file of files) {
        if (file.size > 25 * 1024 * 1024) throw new Error(`${file.name} 超过 25 MB，请先压缩。`);
        setMessage(`正在上传并处理 ${file.name}…`);
        const asset = await upload(file);
        await post(`collections/${work.id}/photos/`, {
          asset_id: asset.id,
          caption: file.name.replace(/\.[^.]+$/, ''),
          position: order++,
        });
        const result = await api<Collection>(`collections/${work.id}/`);
        setWork(result);
      }
      setMessage('照片已添加，点击图片说明可进一步编辑。');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
      if (photoInput.current) photoInput.current.value = '';
    }
  }
  async function workflow(action: string) {
    if (!work) return;
    if (
      action === 'revise' &&
      !window.confirm('撤回后作品会停止公开展示，修改完成后需要重新审核。确定撤回吗？')
    )
      return;
    if (dirty) {
      setError('请先保存尚未保存的修改。');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const result = await post<Collection>(`collections/${work.id}/workflow/`, { action });
      setWork(result);
      setMessage(action === 'submit' ? '已提交审核。' : '已撤回草稿。');
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove(photo: Photo) {
    if (!work || !window.confirm('确定从作品中移除这张照片吗？原始文件仍会保留。')) return;
    setBusy(true);
    try {
      await post(`collections/${work.id}/remove-photo/`, { photo_id: photo.id });
      setWork(await api<Collection>(`collections/${work.id}/`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function updateCaption(photo: Photo, caption: string, position?: number) {
    if (
      !work ||
      (caption === photo.caption && (position === undefined || position === photo.position))
    )
      return;
    setBusy(true);
    try {
      await post(`collections/${work.id}/update-photo/`, {
        photo_id: photo.id,
        caption,
        ...(position !== undefined ? { position } : {}),
      });
      setWork(await api<Collection>(`collections/${work.id}/`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (loading || !user.authenticated)
    return (
      <p className="loading-state" role="status">
        正在确认身份…
      </p>
    );
  if (!user.member)
    return (
      <div className="auth-shell">
        <h1>需要成员身份</h1>
        <p>请联系协会管理员确认成员权限。</p>
        <Link href="/dashboard" className="button">
          返回成员中心
        </Link>
      </div>
    );
  return (
    <div className="container editor-shell">
      <PageHeading
        title={work ? '整理你的作品' : '创建一组作品'}
        description="把照片放在一起，也把想说的话留下。"
      />
      <Link className="back-link" href="/dashboard">
        返回我的作品
      </Link>
      <div aria-live="polite">
        {error && <p className="form-message error">{error}</p>}
        {message && <p className="form-message">{message}</p>}
      </div>
      {!ready ? (
        <p role="status">正在读取作品…</p>
      ) : (
        <>
          <div className="status-line">
            {work && <span className="badge">{statusLabel[work.status]}</span>}
            {work?.review_note && <span className="muted">审核意见：{work.review_note}</span>}
          </div>
          <form ref={form} onSubmit={save} onChange={() => setDirty(true)} key={work?.id || 'new'}>
            <div className="field">
              <label htmlFor="work-title">作品系列名称</label>
              <input
                id="work-title"
                name="title"
                defaultValue={work?.title}
                maxLength={140}
                required
                disabled={!editable || busy}
                placeholder="给这组作品一个名字…"
              />
            </div>
            <div className="field">
              <label htmlFor="work-description">创作说明</label>
              <textarea
                id="work-description"
                name="description"
                defaultValue={work?.description}
                maxLength={16000}
                disabled={!editable || busy}
                placeholder="拍摄的缘由、地点，或者你想表达的感受…"
              />
            </div>
            <div className="field">
              <label htmlFor="work-visibility">展示范围</label>
              <select
                id="work-visibility"
                name="visibility"
                defaultValue={work?.visibility || 'public'}
                disabled={!editable || busy}
              >
                <option value="public">审核后公开展示</option>
                <option value="members">审核后仅成员可见</option>
                <option value="private">仅作者与编辑可见</option>
              </select>
            </div>
            <EventPicker initialValue={work?.event} disabled={!editable || busy} />
            <fieldset
              style={{ border: 0, padding: 0, margin: '0 0 20px' }}
              disabled={!editable || busy}
            >
              <legend style={{ fontSize: 13 }}>主题标签</legend>
              <div className="form-actions">
                {tags.map((tag) => (
                  <label className="checkbox" key={tag}>
                    <input
                      type="checkbox"
                      name="tags"
                      value={tag}
                      defaultChecked={work?.tags.includes(tag)}
                    />
                    {tag}
                  </label>
                ))}
              </div>
            </fieldset>
            {editable && (
              <button className="button" disabled={busy}>
                {busy ? '正在处理…' : '保存草稿'}
              </button>
            )}
            {dirty && <p className="unsaved-note">有尚未保存的修改。</p>}
          </form>
          {work && (
            <section>
              <h2 className="section-title">照片 / {work.photos.length} 张</h2>
              {editable && (
                <div className="upload-zone">
                  <label htmlFor="photo-files">添加照片</label>
                  <input
                    ref={photoInput}
                    id="photo-files"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    onChange={addPhotos}
                    disabled={busy}
                  />
                  <p className="muted">
                    JPEG、PNG、WebP；每张最多 25 MB。展示图会移除位置数据，原片保持私有。
                  </p>
                </div>
              )}
              <div className="upload-list">
                {editable && (
                  <UploadedImages
                    collectionId={work.id}
                    disabled={busy}
                    onAdded={async () => setWork(await api<Collection>(`collections/${work.id}/`))}
                  />
                )}
                {work.photos.map((photo) => (
                  <div className="upload-item" key={photo.id}>
                    {photo.thumbnail_url && (
                      <img src={photo.thumbnail_url} width={100} height={75} alt={photo.caption} />
                    )}
                    <div className="field">
                      <label htmlFor={`caption-${photo.id}`}>图片说明</label>
                      <input
                        id={`caption-${photo.id}`}
                        defaultValue={photo.caption}
                        maxLength={300}
                        required
                        disabled={!editable || busy}
                        onBlur={(e) => updateCaption(photo, e.target.value)}
                      />
                    </div>
                    <div className="field photo-order">
                      <label htmlFor={`position-${photo.id}`}>顺序</label>
                      <input
                        id={`position-${photo.id}`}
                        type="number"
                        min={0}
                        max={9999}
                        defaultValue={photo.position}
                        disabled={!editable || busy}
                        onBlur={(event) =>
                          updateCaption(photo, photo.caption, Number(event.target.value))
                        }
                      />
                    </div>
                    {editable && (
                      <button
                        className="button secondary"
                        disabled={busy}
                        onClick={() => remove(photo)}
                      >
                        移除
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="form-actions" style={{ marginTop: 30 }}>
                {editable ? (
                  <button
                    className="button"
                    disabled={busy || work.photos.length === 0}
                    onClick={() => workflow('submit')}
                  >
                    提交审核
                  </button>
                ) : (
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={() => workflow('revise')}
                  >
                    撤回草稿并修改
                  </button>
                )}
                <Link className="text-link" href={`/works/${work.id}`}>
                  查看作品页面
                </Link>
              </div>
              <p className="muted" style={{ marginTop: 15 }}>
                提交即确认拥有作品展示权及必要的肖像授权。发布后修改需要先撤回，再次提交审核。
              </p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
