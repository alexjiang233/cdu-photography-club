import Link from 'next/link';
import { ArrowDown, ArrowUpRight } from 'lucide-react';
import { serverApi } from '@/lib/server-api';
import type { ArchiveDocument, ClubEvent, Collection, Page } from '@/lib/types';
import { DemoBadge, DocumentRow, Empty, EventRow, WorkCard } from '@/components/ui';
export default async function Home() {
  const [works, events, docs] = await Promise.all([
    serverApi<Page<Collection>>('collections/?featured=1'),
    serverApi<Page<ClubEvent>>('events/'),
    serverApi<Page<ArchiveDocument>>('documents/'),
  ]);
  const hero = works.results[0];
  const photo = hero?.photos[0];
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-heading">
          <div>
            <p className="hero-intro">摄影，是我们与世界相处的方式。</p>
            <h1>
              在日常里，
              <br />
              <span>看见。</span>
            </h1>
          </div>
          <div className="hero-aside">
            <p>
              一次按下快门，
              <br />
              一个值得被记住的瞬间。
              <br />
              在这里，分享所见，也遇见彼此。
            </p>
            <Link className="text-link" href="/works">
              走进作品馆 <ArrowUpRight size={21} aria-hidden="true" />
            </Link>
          </div>
        </div>
        <div className="hero-photo">
          {photo?.display_url ? (
            <Link href={`/works/${hero.id}`} aria-label={`查看作品：${hero.title}`}>
              <img
                src={photo.display_url}
                alt={photo.caption}
                width={photo.width || 1600}
                height={photo.height || 1000}
                fetchPriority="high"
              />
            </Link>
          ) : (
            <div className="hero-empty">
              <p>下一幅画面，等待你的作品。</p>
              <Link href="/dashboard/submit">提交作品</Link>
            </div>
          )}
        </div>
        <div className="hero-caption">
          <span>{hero ? `${hero.title} / ${hero.author.display_name}` : '摄影协会作品展厅'}</span>
          {hero?.is_demo && <DemoBadge />}
          <a href="#selected" className="scroll-hint">
            向下浏览 <ArrowDown size={15} aria-hidden="true" />
          </a>
        </div>
      </section>
      <section className="section" id="selected">
        <div className="section-heading">
          <div>
            <p className="section-subtitle">不同的视角，同样的热爱</p>
            <h2>一些被留下的瞬间</h2>
          </div>
          <Link className="text-link" href="/works">
            全部作品 <ArrowUpRight size={20} aria-hidden="true" />
          </Link>
        </div>
        {works.results.length ? (
          <div className="curated-grid">
            {works.results.slice(1, 4).map((work) => (
              <WorkCard work={work} key={work.id} />
            ))}
          </div>
        ) : (
          <Empty />
        )}
      </section>
      <section className="section events-section">
        <div className="section-heading">
          <div>
            <p className="section-subtitle">带上相机，也带上好奇心</p>
            <h2>一起，走出去</h2>
          </div>
          <Link className="text-link" href="/events">
            全部活动 <ArrowUpRight size={20} aria-hidden="true" />
          </Link>
        </div>
        {events.results.length ? (
          events.results.slice(0, 3).map((event) => <EventRow event={event} key={event.id} />)
        ) : (
          <Empty title="新的活动正在准备中" />
        )}
      </section>
      <section className="section archive-preview">
        <div className="archive-intro">
          <h2>
            影像之外，
            <br />
            经验也值得留下。
          </h2>
          <p>
            从拍摄心得到活动记录，
            <br />
            让每一次分享成为下一次创作的起点。
          </p>
          <Link className="text-link" href="/archive">
            浏览资料库 <ArrowUpRight size={20} aria-hidden="true" />
          </Link>
        </div>
        <div>
          {docs.results.length ? (
            docs.results.slice(0, 3).map((doc) => <DocumentRow key={doc.id} document={doc} />)
          ) : (
            <Empty title="资料库等待第一份分享" />
          )}
        </div>
      </section>
      <section className="join-banner">
        <p>无论使用相机，还是手机</p>
        <h2>你的视角，就很特别。</h2>
        <Link className="button" href="/about#join">
          认识摄影协会 <ArrowUpRight size={18} aria-hidden="true" />
        </Link>
      </section>
    </div>
  );
}
