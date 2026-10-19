'use client';
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useSession } from './session-provider';
import { api, post } from '@/lib/client-api';
import type { Dashboard as DashboardData } from '@/lib/types';
import { date, statusLabel } from '@/lib/format';
import { AccountForms } from './auth-forms';
import { Empty, PageHeading } from './ui';
export function Dashboard() {
  const { user, loading, refresh } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const tab = params.get('tab') || 'works';
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = async () => {
    try {
      setData(await api<DashboardData>('dashboard/'));
    } catch (err) {
      setError((err as Error).message);
    }
  };
  useEffect(() => {
    if (!loading && !user.authenticated) router.replace('/login?next=/dashboard');
    if (user.authenticated) load();
  }, [loading, user.authenticated]);
  async function logout() {
    setBusy(true);
    try {
      await post('auth/logout/', {});
      await refresh();
      router.push('/');
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (loading || !user.authenticated)
    return (
      <div className="container loading-state" role="status">
        正在确认成员身份…
      </div>
    );
  return (
    <div className="container">
      <PageHeading
        title={`${user.profile?.display_name || user.username}，你好`}
        description={
          user.member
            ? '在这里整理作品，查看活动与协会消息。'
            : '账号已登录。成员身份待管理员确认，部分操作暂不可用。'
        }
      >
        <button className="button secondary" onClick={logout} disabled={busy}>
          退出登录
        </button>
      </PageHeading>
      <nav className="dashboard-tabs" aria-label="成员中心栏目">
        {[
          ['works', '我的作品'],
          ['events', '我的活动'],
          ['account', '个人设置'],
        ].map(([value, label]) => (
          <Link
            className={tab === value ? 'active' : ''}
            key={value}
            href={`/dashboard?tab=${value}`}
          >
            {label}
          </Link>
        ))}
        <Link href="/archive">内部资料</Link>
        {user.staff && <a href="/admin/">管理后台</a>}
      </nav>
      {error && (
        <p className="form-message error" role="alert">
          {error}
        </p>
      )}
      <div className="dashboard-layout">
        <section>
          {tab === 'account' ? (
            <AccountForms />
          ) : tab === 'events' ? (
            data?.registrations.length ? (
              data.registrations.map((record) => (
                <article className="dashboard-item" key={record.id}>
                  <div>
                    <h3>
                      <Link href={`/events/${record.event_id}`}>{record.title}</Link>
                    </h3>
                    <p>
                      {date(record.starts_at)} / {record.cancelled ? '已取消' : '已报名'}
                    </p>
                  </div>
                  <Link className="button secondary" href={`/events/${record.event_id}`}>
                    查看活动
                  </Link>
                </article>
              ))
            ) : (
              <Empty title="还没有报名记录">
                <Link className="button secondary" href="/events">
                  看看有哪些活动
                </Link>
              </Empty>
            )
          ) : (
            <>
              <div className="form-actions" style={{ marginBottom: 20 }}>
                {user.member && (
                  <Link className="button" href="/dashboard/submit">
                    创建作品系列
                  </Link>
                )}
                {user.can_edit_documents && (
                  <Link className="button secondary" href="/admin/club/document/">
                    管理资料
                  </Link>
                )}
                {user.can_edit_events && (
                  <Link className="button secondary" href="/admin/club/event/">
                    管理活动
                  </Link>
                )}
              </div>
              {data?.collections.length ? (
                data.collections.map((work) => (
                  <article className="dashboard-item" key={work.id}>
                    <div>
                      <h3>{work.title}</h3>
                      <p>
                        {statusLabel[work.status]} / {work.photos.length} 张照片
                      </p>
                      {work.review_note && <p>修改建议：{work.review_note}</p>}
                    </div>
                    <div className="dashboard-item-actions">
                      <Link className="button secondary" href={`/dashboard/submit?id=${work.id}`}>
                        管理作品
                      </Link>
                      <Link className="text-link" href={`/works/${work.id}`}>
                        查看作品
                      </Link>
                    </div>
                  </article>
                ))
              ) : (
                <Empty
                  title="第一组作品，从这里开始"
                  description="把照片整理成系列，写下说明，再提交给编辑审核。"
                />
              )}
            </>
          )}
        </section>
        <aside className="info-panel dashboard-notices">
          <h2>协会消息</h2>
          {data?.notices.length ? (
            data.notices.map((notice) => (
              <article className="notice" key={notice.id}>
                <Link href={notice.href || '/dashboard'}>
                  {!notice.read && '● '}
                  {notice.text}
                </Link>
                <time dateTime={notice.created_at}>{date(notice.created_at)}</time>
              </article>
            ))
          ) : (
            <p className="muted">暂时没有新消息。</p>
          )}
          {data?.notices.some((n) => !n.read) && (
            <button
              className="text-link"
              style={{ border: 0, background: 'none' }}
              onClick={async () => {
                try {
                  await post('dashboard/', {});
                  await load();
                } catch (err) {
                  setError((err as Error).message);
                }
              }}
            >
              全部标记为已读
            </button>
          )}
          <h2 style={{ marginTop: 30 }}>后续功能</h2>
          <p className="muted">
            器材借用、RAW 大文件和文件正文检索暂未开放。当前资料库支持标题、简介与标签查找。
          </p>
        </aside>
      </div>
    </div>
  );
}
