'use client';
import { useEffect, useRef, useState } from 'react';
import { Check, Link2 } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { reducedMotion } from '@/lib/motion';

/** Reveal nodes are visible by default; WAAPI owns only temporary transforms. */
export function MotionRoot() {
  const pathname = usePathname();
  useEffect(() => {
    const scrollDriven = CSS.supports('animation-timeline: view()');
    const seen = new WeakSet<HTMLElement>();
    const animations = new Set<Animation>();
    const waiting = new Map<Element, Animation>();
    const preference = matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const animation = waiting.get(entry.target);
          if (reducedMotion()) animation?.cancel();
          else animation?.play();
          waiting.delete(entry.target);
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.08, rootMargin: '0px 0px -4% 0px' },
    );
    const scan = () => {
      frame = 0;
      document.querySelectorAll<HTMLElement>('[data-reveal]').forEach((el) => {
        if (seen.has(el) || el.closest('[data-layout-grid]')) return;
        seen.add(el);
        if (reducedMotion() || (scrollDriven && el.hasAttribute('data-scroll-reveal'))) return;
        const print = el.dataset.reveal === 'gallery-print';
        const animation = el.animate(
          [
            {
              opacity: 0,
              transform: print ? 'translateY(26px) rotate(.6deg) scale(.985)' : 'translateY(22px)',
            },
            { opacity: 1, transform: 'none' },
          ],
          { duration: print ? 850 : 680, fill: 'both', easing: 'cubic-bezier(.16,1,.3,1)' },
        );
        animations.add(animation);
        animation.onfinish = () => {
          animation.cancel();
          animations.delete(animation);
        };
        if (el.getBoundingClientRect().top >= innerHeight) {
          animation.pause();
          waiting.set(el, animation);
          observer.observe(el);
        }
      });
    };
    const mutations = new MutationObserver(() => {
      if (!frame) frame = requestAnimationFrame(scan);
    });
    mutations.observe(document.getElementById('main') || document.body, {
      subtree: true,
      childList: true,
    });
    const cancel = () => {
      if (reducedMotion()) {
        animations.forEach((a) => a.cancel());
        waiting.clear();
        observer.disconnect();
      }
    };
    preference.addEventListener('change', cancel);
    frame = requestAnimationFrame(scan);
    return () => {
      cancelAnimationFrame(frame);
      mutations.disconnect();
      observer.disconnect();
      animations.forEach((a) => a.cancel());
      preference.removeEventListener('change', cancel);
    };
  }, [pathname]);
  return null;
}

export function CopyLink({ label = '复制链接', href }: { label?: string; href?: string }) {
  const [done, setDone] = useState(false);
  const [show, setShow] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  function confirmCopied() {
    setDone(true);
    setShow(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      setDone(false);
      setShow(false);
    }, 1800);
  }

  async function copy() {
    const url = href ? new URL(href, window.location.origin).href : window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      confirmCopied();
    } catch {
      // 不支持剪贴板 API 时退回选区复制，不弹 prompt
      const field = document.createElement('textarea');
      field.value = url;
      field.setAttribute('readonly', '');
      field.style.position = 'fixed';
      field.style.opacity = '0';
      document.body.appendChild(field);
      field.select();
      try {
        document.execCommand('copy');
      } catch {
        /* 忽略：至少让用户看到链接 */
      }
      field.remove();
      confirmCopied();
    }
  }

  return (
    <>
      <button className="copy-link" onClick={copy} type="button">
        {done ? <Check size={14} aria-hidden="true" /> : <Link2 size={14} aria-hidden="true" />}
        {done ? '已复制' : label}
      </button>
      <div className={`toast ${show ? 'show' : ''}`} role="status" aria-live="polite">
        链接已复制
      </div>
    </>
  );
}
