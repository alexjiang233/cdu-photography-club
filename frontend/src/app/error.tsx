'use client';
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="auth-shell">
      <h1>内容暂时没有打开</h1>
      <p>请检查网络后重试。如果问题持续，请联系协会管理员。</p>
      <button className="button" onClick={reset}>
        重新加载
      </button>
    </div>
  );
}
