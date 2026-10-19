import Link from 'next/link';
export default function Unavailable() {
  return <div className="auth-shell"><h1>当前为网站预览</h1><p>此版本用于浏览页面与公开示例内容。成员登录、投稿、报名和内部资料需要正式服务器，暂未开放，也不会在这里收集账号或个人信息。</p><Link className="button" href="/works">浏览作品馆</Link></div>;
}
