import { Suspense } from 'react';
import type { Metadata } from 'next';
import { LoginForm } from '@/components/auth-forms';
export const metadata: Metadata = { title: '成员登录', robots: { index: false } };
export default function Login() {
  return (
    <div className="auth-shell">
      <h1>回到摄影协会</h1>
      <p>登录后投稿作品、报名活动，查看内部资料。</p>
      <Suspense fallback={<p>正在打开登录表单…</p>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
