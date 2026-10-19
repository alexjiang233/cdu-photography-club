import { Suspense } from 'react';
import type { Metadata } from 'next';
import { ResetForm } from '@/components/auth-forms';
export const metadata: Metadata = { title: '重置密码', robots: { index: false, follow: false } };
export default function Reset() {
  return (
    <div className="auth-shell">
      <h1>重新设置密码</h1>
      <p>使用关联邮箱找回账号。未设置邮箱时，请联系协会管理员。</p>
      <Suspense fallback={<p>正在打开表单…</p>}>
        <ResetForm />
      </Suspense>
    </div>
  );
}
