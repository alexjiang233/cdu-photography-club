'use client';
import { useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import type { Photo } from '@/lib/types';
export function Gallery({ photos }: { photos: Photo[] }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [index, setIndex] = useState(0);
  const [caption, setCaption] = useState('');
  const show = (i: number) => {
    setIndex(i);
    setCaption(photos[i].caption);
    if (!dialog.current?.open) dialog.current?.showModal();
  };
  const current = photos[index];
  return (
    <>
      <div>
        {photos.map((photo, i) => (
          <figure key={photo.id} className="detail-photo">
            <button type="button" onClick={() => show(i)} aria-label={`放大查看：${photo.caption}`}>
              {photo.display_url && (
                <img
                  src={photo.display_url}
                  alt={photo.caption}
                  width={photo.width || 1200}
                  height={photo.height || 800}
                  loading={i === 0 ? 'eager' : 'lazy'}
                />
              )}
            </button>
            <figcaption>{photo.caption}</figcaption>
          </figure>
        ))}
      </div>
      <dialog
        className="lightbox"
        ref={dialog}
        aria-label="作品大图"
        onClick={(e) => {
          if (e.target === e.currentTarget) dialog.current?.close();
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowRight') {
            e.preventDefault();
            show((index + 1) % photos.length);
          }
          if (e.key === 'ArrowLeft') {
            e.preventDefault();
            show((index - 1 + photos.length) % photos.length);
          }
        }}
      >
        <button
          className="icon-button lightbox-close"
          onClick={() => dialog.current?.close()}
          aria-label="关闭大图"
        >
          <X aria-hidden="true" />
        </button>
        {current?.display_url && (
          <img
            className="lightbox-image"
            src={current.display_url}
            alt={current.caption}
            width={current.width || 1200}
            height={current.height || 800}
          />
        )}
        <div className="lightbox-controls">
          <button
            className="icon-button"
            onClick={() => show((index - 1 + photos.length) % photos.length)}
            aria-label="上一张照片"
          >
            <ChevronLeft aria-hidden="true" />
          </button>
          <p className="lightbox-caption" aria-live="polite">
            {caption} / {index + 1} 张，共 {photos.length} 张
          </p>
          <button
            className="icon-button"
            onClick={() => show((index + 1) % photos.length)}
            aria-label="下一张照片"
          >
            <ChevronRight aria-hidden="true" />
          </button>
        </div>
      </dialog>
    </>
  );
}
