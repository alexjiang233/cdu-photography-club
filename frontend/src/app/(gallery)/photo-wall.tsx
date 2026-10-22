'use client';
import { useEffect, useRef, useState } from 'react';
import { Pause, Play } from 'lucide-react';

// Duplicate complete segments, including their trailing gap, for a seamless loop.
const rows = Array.from({ length: 7 }, (_, row) =>
  Array.from({ length: 18 }, (_, column) => ((row * 3 + column) % 13) + 1),
);
export function PhotoWall() {
  const root = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  const [visible, setVisible] = useState(true);
  const [hidden, setHidden] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), {
      threshold: 0.01,
    });
    if (root.current) observer.observe(root.current);
    const visibility = () => setHidden(document.hidden);
    visibility();
    document.addEventListener('visibilitychange', visibility);
    return () => {
      observer.disconnect();
      document.removeEventListener('visibilitychange', visibility);
    };
  }, []);
  return (
    <>
      <div
        ref={root}
        className="wall-scene"
        aria-hidden="true"
        data-paused={paused || !visible || hidden || undefined}
      >
        {rows.map((images, row) => (
          <div className="wall-row" key={row}>
            <div
              className={`wall-track${row % 2 ? ' wall-track-reverse' : ''}`}
              style={{ animationDelay: `${-row * 9}s` }}
            >
              {[0, 1].map((copy) => (
                <div className="wall-segment" key={copy}>
                  {images.map((number, i) => (
                    <img
                      key={i}
                      src={`/gallery-wall/w${String(number).padStart(2, '0')}.jpg`}
                      width="1200"
                      height="800"
                      alt=""
                      decoding="async"
                      fetchPriority={row === 0 && i < 2 && copy === 0 ? 'high' : 'auto'}
                      draggable={false}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button
        type="button"
        className="wall-pause"
        aria-pressed={paused}
        onClick={() => setPaused((value) => !value)}
      >
        {paused ? <Play size={14} aria-hidden="true" /> : <Pause size={14} aria-hidden="true" />}
        <span>{paused ? '继续播放' : '暂停照片墙'}</span>
      </button>
    </>
  );
}
