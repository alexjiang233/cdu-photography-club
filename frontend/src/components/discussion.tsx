'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, post } from '@/lib/client-api';
import { date } from '@/lib/format';
import type { Discussion, Page } from '@/lib/types';
import { useSession } from './session-provider';
export function DiscussionPanel({
  resource,
  id,
}: {
  resource: 'collections' | 'events';
  id: string;
}) {
  const { user, loading } = useSession();
  const [comments, setComments] = useState<Discussion[]>([]);
  const [nextPage, setNextPage] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const load = async (page = 1) => {
    try {
      const data = await api<Page<Discussion>>(`${resource}/${id}/comments/?page=${page}`);
      setComments((old) => (page === 1 ? data.results : [...old, ...data.results]));
      setNextPage(data.next ? page + 1 : null);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  useEffect(() => {
    load();
  }, [id, resource, user.authenticated]); // refresh pending comments after sign-in
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    const form = event.currentTarget;
    try {
      await post(`${resource}/${id}/comments/`, { text: new FormData(form).get('text') });
      form.reset();
      setMessage('已提交，审核通过后公开显示。');
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="discussion">
      <h2>{resource === 'collections' ? '围绕这组作品，聊一聊' : '活动提问与交流'}</h2>
      {comments.map((comment) => (
        <article className="comment" key={comment.id}>
          <div className="comment-meta">
            <span>
              {comment.author_name}
              {!comment.approved && ' / 等待审核'}
            </span>
            <time dateTime={comment.created_at}>{date(comment.created_at)}</time>
          </div>
          <p>{comment.text}</p>
        </article>
      ))}
      {nextPage && (
        <button className="button secondary" onClick={() => load(nextPage)}>
          查看更早的讨论
        </button>
      )}
      {!comments.length && <p className="muted">还没有讨论。可以分享观察，也可以提出具体问题。</p>}
      <div aria-live="polite">
        {error && <p className="form-message error">{error}</p>}
        {message && <p className="form-message">{message}</p>}
      </div>
      {!loading &&
        (user.member ? (
          <form onSubmit={submit} style={{ marginTop: 25 }}>
            <div className="field">
              <label htmlFor="comment-text">你的想法</label>
              <textarea
                id="comment-text"
                name="text"
                required
                maxLength={2000}
                placeholder="分享你的观察，或提出一个问题…"
              />
            </div>
            <button className="button" disabled={busy}>
              {busy ? '正在提交…' : '提交讨论'}
            </button>
          </form>
        ) : (
          <p className="muted" style={{ marginTop: 25 }}>
            <Link className="text-link" href="/login">
              以协会成员身份登录后参与交流
            </Link>
          </p>
        ))}
    </section>
  );
}
