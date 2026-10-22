'use client';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { reducedMotion } from '@/lib/motion';
import Link from 'next/link';
import type { Collection } from '@/lib/types';

export function PhotoBrowser({ albums }: { albums: Collection[] }) {
  const grid = useRef<HTMLDivElement>(null);
  const previous = useRef(new Map<string, DOMRect>());
  const running = useRef(new Set<Animation>());
  const [albumId, setAlbumId] = useState('');
  const [query, setQuery] = useState('');
  const photos = useMemo(
    () =>
      albums
        .filter((a) => !albumId || a.id === albumId)
        .flatMap((a) =>
          a.photos
            .filter(
              (p) =>
                p.display_url &&
                `${a.title} ${p.caption} ${p.shooting?.photographer || ''}`
                  .toLowerCase()
                  .includes(query.trim().toLowerCase()),
            )
            .map((p) => ({ photo: p, album: a })),
        ),
    [albums, albumId, query],
  );
  const rememberPositions = () => {
    running.current.forEach((animation) => animation.cancel());
    running.current.clear();
    previous.current = new Map(
      Array.from(grid.current?.querySelectorAll<HTMLElement>('[data-photo-id]') || []).map((el) => [
        el.dataset.photoId!,
        el.getBoundingClientRect(),
      ]),
    );
  };
  useLayoutEffect(() => {
    if (reducedMotion()) return;
    const animations = running.current;
    grid.current?.querySelectorAll<HTMLElement>('[data-photo-id]').forEach((el, i) => {
      const old = previous.current.get(el.dataset.photoId!);
      const next = el.getBoundingClientRect();
      const animation = el.animate(
        old
          ? [
              { transform: `translate(${old.left - next.left}px, ${old.top - next.top}px)` },
              { transform: 'none' },
            ]
          : [
              { opacity: 0, transform: 'translateY(14px) scale(.985)' },
              { opacity: 1, transform: 'none' },
            ],
        {
          duration: old ? 420 : 480,
          delay: old ? 0 : Math.min(i, 4) * 35,
          easing: 'cubic-bezier(.22,1,.36,1)',
          fill: 'both',
        },
      );
      animations.add(animation);
      animation.onfinish = () => {
        animation.cancel();
        animations.delete(animation);
      };
    });
    return () => {
      animations.forEach((animation) => animation.cancel());
      animations.clear();
    };
  }, [photos]);
  useEffect(() => {
    const cancel = () => {
      if (reducedMotion()) {
        running.current.forEach((animation) => animation.cancel());
        running.current.clear();
      }
    };
    const preference = matchMedia('(prefers-reduced-motion: reduce)');
    preference.addEventListener('change', cancel);
    window.addEventListener('photo:motion-change', cancel);
    return () => {
      preference.removeEventListener('change', cancel);
      window.removeEventListener('photo:motion-change', cancel);
    };
  }, []);
  return (
    <>
      <div className="gl-browse-tools">
        <label>
          按相册浏览
          <select
            aria-label="按相册浏览"
            value={albumId}
            onChange={(e) => {
              rememberPositions();
              setAlbumId(e.target.value);
            }}
          >
            <option value="">全部相册</option>
            {albums.map((a) => (
              <option key={a.id} value={a.id}>
                {a.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          找一张照片
          <input
            type="search"
            value={query}
            onChange={(e) => {
              rememberPositions();
              setQuery(e.target.value);
            }}
            placeholder="相册、图注、作者"
          />
        </label>
        <p aria-live="polite">{photos.length} 张照片</p>
      </div>
      <div className="gl-photo-browser" ref={grid} data-layout-grid>
        {photos.map(({ photo, album }) => (
          <figure key={photo.id} data-photo-id={photo.id}>
            <Link href={`/works/${album.id}?photo=${photo.id}`} className="gl-browse-frame">
              <img
                src={photo.display_url!}
                alt={photo.caption || album.title}
                width={photo.width || 1200}
                height={photo.height || 800}
                loading="lazy"
              />
            </Link>
            <figcaption>
              <Link href={`/works/${album.id}?photo=${photo.id}`}>
                {photo.caption || album.title}
              </Link>
              {photo.caption && photo.caption !== album.title && <span>{album.title}</span>}
            </figcaption>
          </figure>
        ))}
      </div>
      {!photos.length && (
        <p className="wall-empty">没有找到照片。试试其他关键词，或切换到全部相册。</p>
      )}
    </>
  );
}
