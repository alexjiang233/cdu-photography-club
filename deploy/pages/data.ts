import raw from './demo.json';
import type { ArchiveDocument, ClubEvent, Collection, Profile, Site } from '@/lib/types';
const base = process.env.NEXT_PUBLIC_BASE_PATH || '';
function paths(value: unknown): unknown {
  if (typeof value === 'string' && value.startsWith('/preview-media/')) return base + value;
  if (Array.isArray(value)) return value.map(paths);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, paths(v)]));
  return value;
}
export const demo = paths(raw) as {
  site: Site; members: Profile[]; collections: Collection[]; events: ClubEvent[]; documents: ArchiveDocument[];
};
export function readPreview(path: string): unknown {
  const url = new URL(path, 'https://preview.invalid/');
  const [resource, id, action] = url.pathname.split('/').filter(Boolean);
  if (resource === 'auth' && id === 'session') return { authenticated: false };
  if (action === 'comments') return { count: 0, results: [], next: null, previous: null };
  if (resource === 'site') return demo.site;
  if (resource === 'members') return id ? demo.members.find(row => row.id === id) : demo.members;
  if (!['collections', 'events', 'documents'].includes(resource)) throw new Error('此功能需要正式服务器，静态预览暂不开放。');
  let rows = [...demo[resource as 'collections' | 'events' | 'documents']];
  if (id) return rows.find(row => row.id === id);
  const q = (url.searchParams.get('q') || '').trim().toLocaleLowerCase();
  rows = rows.filter(row => (!q || [row.title, row.description, ...row.tags].join(' ').toLocaleLowerCase().includes(q)) &&
    (!url.searchParams.get('event') || row.event === url.searchParams.get('event')));
  if (resource === 'collections') rows = (rows as Collection[]).filter(row =>
    (!url.searchParams.get('tag') || row.tags.includes(url.searchParams.get('tag')!)) &&
    (!url.searchParams.get('author') || row.author.id === url.searchParams.get('author')) &&
    (!url.searchParams.get('featured') || row.featured));
  if (resource === 'documents') rows = (rows as ArchiveDocument[]).filter(row =>
    (!url.searchParams.get('year') || String(row.year) === url.searchParams.get('year')) &&
    (!url.searchParams.get('category') || row.category === url.searchParams.get('category')));
  return { count: rows.length, next: null, previous: null, results: rows };
}
