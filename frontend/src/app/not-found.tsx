import Link from 'next/link';
export default function NotFound() {
  return (
    <div className="auth-shell">
      <h1>这幅画面还未展出</h1>
      <p>内容可能已撤下，或需要相应的成员权限。</p>
      <Link className="button" href="/works">
        返回作品馆
      </Link>
      <div className="auth-links">
        <Link href="/login">成员登录</Link>
        <Link href="/">回到首页</Link>
      </div>
    </div>
  );
}
