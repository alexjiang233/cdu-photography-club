'use client';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import type { Photo } from '@/lib/types';
import { reducedMotion } from '@/lib/motion';
import { PhotoFacts } from './photo-facts';
export function Gallery({ photos, initialIndex = 0 }: { photos: Photo[]; initialIndex?: number }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const touch = useRef<{ x: number; y: number } | null>(null);
  const image = useRef<HTMLImageElement>(null);
  const animation = useRef<Animation | null>(null);
  const origin = useRef<DOMRect | null>(null);
  const direction = useRef(0);
  const closing = useRef(false);
  const [index, setIndex] = useState(Math.max(0, Math.min(initialIndex, photos.length - 1)));
  const [open, setOpen] = useState(false);
  const current = photos[index];
  const show = (i: number, source?: HTMLButtonElement) => {
    closing.current = false;
    if (source) {
      origin.current = source.querySelector('img')?.getBoundingClientRect() || null;
      direction.current = 0;
    }
    setIndex(i);
    setOpen(true);
    if (!dialog.current?.open) dialog.current?.showModal();
  };
  const step = (delta: number) => {
    if (photos.length < 2) return;
    direction.current = delta;
    show((index + delta + photos.length) % photos.length);
  };
  const close = () => {
    const el = dialog.current;
    if (!el || closing.current) return;
    closing.current = true;
    animation.current?.cancel();
    if (reducedMotion()) {
      el.close();
      return;
    }
    const exit = el.animate(
      [
        { opacity: 1, transform: 'scale(1)' },
        { opacity: 0, transform: 'scale(.98)' },
      ],
      { duration: 150, easing: 'ease-out' },
    );
    exit.onfinish = () => {
      el.close();
      exit.cancel();
    };
  };
  useEffect(() => {
    if (!open) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = overflow;
      animation.current?.cancel();
    };
  }, [open]);
  useLayoutEffect(() => {
    const el = image.current;
    if (!open || !el || reducedMotion()) return;
    animation.current?.cancel();
    const target = el.getBoundingClientRect();
    const source = origin.current;
    const transform = direction.current
      ? `translateX(${direction.current * 36}px) scale(.99)`
      : source
        ? `translate(${source.left + source.width / 2 - target.left - target.width / 2}px, ${source.top + source.height / 2 - target.top - target.height / 2}px) scale(${Math.max(0.2, Math.min(1, source.width / target.width))})`
        : 'scale(.96)';
    animation.current = el.animate(
      [
        { opacity: direction.current ? 0 : 0.5, transform },
        { opacity: 1, transform: 'none' },
      ],
      { duration: direction.current ? 260 : 380, easing: 'cubic-bezier(.16,1,.3,1)' },
    );
  }, [index, open]);
  return (
    <>
      {current && (
        <div className="photo-detail-layout" key={current.id} data-reveal="gallery-card">
          <figure className="ex-plate">
            <button
              className="ex-photo-button"
              type="button"
              onClick={(event) => show(index, event.currentTarget)}
              aria-label={`放大查看：${current.caption}`}
            >
              {current.display_url && (
                <img
                  src={current.display_url}
                  alt={current.caption}
                  width={current.width || 1200}
                  height={current.height || 800}
                  fetchPriority="high"
                />
              )}
            </button>
            <figcaption className="ex-caption">
              <span className="ex-plate-number">{String(index + 1).padStart(2, '0')}</span>
              <span>{current.caption}</span>
            </figcaption>
          </figure>
          <aside className="photo-detail-aside">
            <h2>{current.caption}</h2>
            <PhotoFacts photo={current} />
          </aside>
        </div>
      )}
      {photos.length > 1 && (
        <nav className="photo-contact-sheet" aria-label="选择照片">
          {photos.map((photo, i) => (
            <button
              type="button"
              key={photo.id}
              aria-label={`查看第${i + 1}张：${photo.caption}`}
              aria-pressed={index === i}
              onClick={(event) => {
                setIndex(i);
                event.currentTarget.scrollIntoView({
                  behavior: reducedMotion() ? 'instant' : 'smooth',
                  block: 'nearest',
                  inline: 'center',
                });
              }}
            >
              {photo.thumbnail_url || photo.display_url ? (
                <img
                  src={photo.thumbnail_url || photo.display_url || ''}
                  alt=""
                  width={photo.width || 1200}
                  height={photo.height || 800}
                  loading="lazy"
                />
              ) : null}
              <span>{String(i + 1).padStart(2, '0')}</span>
            </button>
          ))}
        </nav>
      )}
      <dialog
        className="lightbox lightbox-with-facts"
        ref={dialog}
        aria-label="作品大图"
        onClick={(e) => {
          if (e.target === e.currentTarget) close();
        }}
        onCancel={(event) => {
          event.preventDefault();
          close();
        }}
        onClose={() => {
          setOpen(false);
          closing.current = false;
        }}
        onTouchStart={(event) => {
          const point = event.touches[0];
          touch.current =
            event.touches.length === 1 && point ? { x: point.clientX, y: point.clientY } : null;
        }}
        onTouchCancel={() => {
          touch.current = null;
        }}
        onTouchEnd={(event) => {
          const start = touch.current;
          touch.current = null;
          const end = event.changedTouches[0];
          if (!start || !end) return;
          const dx = end.clientX - start.x,
            dy = end.clientY - start.y;
          if (Math.abs(dx) > 56 && Math.abs(dx) > Math.abs(dy) * 1.3) step(dx > 0 ? -1 : 1);
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowRight') {
            e.preventDefault();
            step(1);
          }
          if (e.key === 'ArrowLeft') {
            e.preventDefault();
            step(-1);
          }
        }}
      >
        <button className="icon-button lightbox-close" onClick={close} aria-label="关闭大图">
          <X aria-hidden="true" />
        </button>
        {current?.display_url && (
          <div className="lightbox-stage">
            <img
              key={current.id}
              ref={image}
              className="lightbox-image"
              src={current.display_url}
              alt={current.caption}
              width={current.width || 1200}
              height={current.height || 800}
            />
            <aside className="lightbox-facts">
              <h2>{current.caption}</h2>
              <PhotoFacts photo={current} />
            </aside>
          </div>
        )}
        <div className="lightbox-controls">
          <button
            className="icon-button"
            disabled={photos.length < 2}
            onClick={() => step(-1)}
            aria-label="上一张照片"
          >
            <ChevronLeft aria-hidden="true" />
          </button>
          <p className="lightbox-caption" aria-live="polite">
            {current?.caption} / {index + 1} 张，共 {photos.length} 张
          </p>
          <button
            className="icon-button"
            disabled={photos.length < 2}
            onClick={() => step(1)}
            aria-label="下一张照片"
          >
            <ChevronRight aria-hidden="true" />
          </button>
        </div>
      </dialog>
    </>
  );
}
