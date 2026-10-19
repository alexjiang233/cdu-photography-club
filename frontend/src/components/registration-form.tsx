'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { post } from '@/lib/client-api';
import { useSession } from './session-provider';
import type { ClubEvent } from '@/lib/types';
export function RegistrationForm({ event }: { event: ClubEvent }) {
  const { user, loading } = useSession();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = new FormData(e.currentTarget);
      await post(`events/${event.id}/register/`, {
        contact: data.get('contact'),
        note: data.get('note'),
      });
      setMessage('报名成功，可在成员中心查看记录。');
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function cancel() {
    if (!window.confirm('确定取消这次活动报名吗？')) return;
    setBusy(true);
    setError('');
    try {
      await post(`events/${event.id}/cancel-registration/`, {});
      setMessage('已取消报名。');
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (event.is_demo) return <p className="form-message">这是示例活动，暂不接受真实报名。</p>;
  if (loading)
    return (
      <p className="muted" role="status">
        正在确认报名状态…
      </p>
    );
  return (
    <>
      {error && (
        <p className="form-message error" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="form-message" role="status">
          {message}
        </p>
      )}
      {event.my_registration ? (
        <div>
          <p className="form-message">你已报名本次活动。</p>
          {new Date(event.starts_at) > new Date() && (
            <button className="button secondary" disabled={busy} onClick={cancel}>
              取消报名
            </button>
          )}
        </div>
      ) : !event.registration_open || new Date(event.registration_deadline) <= new Date() ? (
        <p className="muted">当前活动报名已关闭。</p>
      ) : !user.authenticated ? (
        <Link className="button" href={`/login?next=/events/${event.id}`}>
          登录后报名
        </Link>
      ) : !user.member ? (
        <p className="muted">报名需要有效的协会成员身份，请联系管理员确认。</p>
      ) : event.registration_count >= event.capacity ? (
        <p className="muted">本次活动名额已满。</p>
      ) : (
        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="contact">联系方式</label>
            <input
              id="contact"
              name="contact"
              required
              maxLength={120}
              autoComplete="tel"
              placeholder="手机号或其他可联系到你的方式…"
            />
            <small>仅你和活动管理人员可以查看。</small>
          </div>
          <div className="field">
            <label htmlFor="registration-note">报名备注（可选）</label>
            <textarea
              id="registration-note"
              name="note"
              maxLength={500}
              placeholder="例如器材或其他需要说明的事项…"
            />
          </div>
          <button className="button" disabled={busy}>
            {busy ? '正在报名…' : '确认报名'}
          </button>
        </form>
      )}
    </>
  );
}
