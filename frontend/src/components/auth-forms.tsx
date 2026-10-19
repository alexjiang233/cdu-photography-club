'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api, post } from '@/lib/client-api';
import { useSession } from './session-provider';
export function LoginForm() {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useSession();
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const data = new FormData(e.currentTarget);
    try {
      await post('auth/login/', {
        username: data.get('username'),
        password: data.get('password'),
        otp: data.get('otp'),
      });
      await refresh();
      const next = params.get('next');
      router.push(
        next?.startsWith('/') && !next.startsWith('//') && !next.includes('\\')
          ? next
          : '/dashboard',
      );
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit}>
      <div className="field">
        <label htmlFor="username">成员账号</label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          spellCheck={false}
          required
          maxLength={150}
        />
      </div>
      <div className="field">
        <label htmlFor="password">密码</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </div>
      <details style={{ marginBottom: 20 }}>
        <summary className="muted">管理员动态验证码</summary>
        <div className="field" style={{ marginTop: 12 }}>
          <label htmlFor="otp">六位验证码</label>
          <input
            id="otp"
            name="otp"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            pattern="[0-9]{6}"
          />
          <small>正式环境管理员账号需要验证码。</small>
        </div>
      </details>
      {error && (
        <p className="form-message error" role="alert">
          {error}
        </p>
      )}
      <button className="button" disabled={busy}>
        {busy ? '正在登录…' : '登录成员中心'}
      </button>
      <div className="auth-links">
        <Link href="/reset-password">忘记密码</Link>
        <Link href="/about#join">了解如何加入</Link>
      </div>
    </form>
  );
}
export function ResetForm() {
  const params = useSearchParams();
  const token = params.get('token');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = new FormData(e.currentTarget);
      if (token && data.get('password') !== data.get('confirm'))
        throw new Error('两次密码不一致。');
      const response = await post<{ detail: string }>(
        'auth/reset-password/',
        token
          ? { uid: params.get('uid'), token, password: data.get('password') }
          : { email: data.get('email') },
      );
      setMessage(response.detail);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit}>
      {token ? (
        <>
          <div className="field">
            <label htmlFor="reset-new">新密码</label>
            <input
              id="reset-new"
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
            />
            <small>至少 12 位，避免常见密码。</small>
          </div>
          <div className="field">
            <label htmlFor="reset-confirm">再次输入密码</label>
            <input
              id="reset-confirm"
              name="confirm"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
            />
          </div>
        </>
      ) : (
        <div className="field">
          <label htmlFor="reset-email">账号关联邮箱</label>
          <input
            id="reset-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            spellCheck={false}
          />
        </div>
      )}
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
      <button className="button" disabled={busy}>
        {busy ? '正在处理…' : token ? '设置新密码' : '发送重置邮件'}
      </button>
      <div className="auth-links">
        <Link href="/login">返回登录</Link>
      </div>
    </form>
  );
}
export function AccountForms() {
  const { user, refresh } = useSession();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function profile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setMessage('');
    setError('');
    try {
      const data = new FormData(e.currentTarget);
      await api('auth/account/', {
        method: 'PATCH',
        body: JSON.stringify({
          display_name: data.get('display_name'),
          bio: data.get('bio'),
          cohort: data.get('cohort'),
          is_public: data.get('is_public') === 'on',
        }),
      });
      await refresh();
      setMessage('个人资料已保存。');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function password(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setMessage('');
    setError('');
    const form = e.currentTarget;
    try {
      const data = new FormData(form);
      if (data.get('new_password') !== data.get('confirm')) throw new Error('两次密码不一致。');
      await post('auth/account/', {
        current_password: data.get('current_password'),
        new_password: data.get('new_password'),
      });
      form.reset();
      setMessage('密码已修改。');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="profile-form">
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
      <form onSubmit={profile} key={user.profile?.id}>
        <div className="field">
          <label htmlFor="display-name">作品署名</label>
          <input
            id="display-name"
            name="display_name"
            defaultValue={user.profile?.display_name || user.username}
            maxLength={60}
            autoComplete="nickname"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="cohort">届别（可选）</label>
          <input
            id="cohort"
            name="cohort"
            defaultValue={user.profile?.cohort}
            maxLength={20}
            placeholder="例如 2026 级…"
          />
        </div>
        <div className="field">
          <label htmlFor="bio">个人简介</label>
          <textarea id="bio" name="bio" defaultValue={user.profile?.bio} maxLength={2000} />
        </div>
        <label className="checkbox">
          <input type="checkbox" name="is_public" defaultChecked={user.profile?.is_public} />
          公开我的作者主页
        </label>
        <button className="button" disabled={busy}>
          保存个人资料
        </button>
      </form>
      <h2 className="section-title">修改密码</h2>
      <form onSubmit={password}>
        <div className="field">
          <label htmlFor="current-password">当前密码</label>
          <input
            id="current-password"
            type="password"
            name="current_password"
            autoComplete="current-password"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="new-password">新密码</label>
          <input
            id="new-password"
            name="new_password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="confirm-password">确认新密码</label>
          <input
            id="confirm-password"
            name="confirm"
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
          />
        </div>
        <button className="button secondary" disabled={busy}>
          修改密码
        </button>
      </form>
    </div>
  );
}
