// Isolated hosting adapter: reuse application views without changing server deployment.
import { cp, mkdir, readFile, writeFile, access, symlink } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const build = path.join(root, '.pages-build', 'frontend');
const source = path.join(root, 'frontend');
const basePath = process.env.PAGES_BASE_PATH || '/cdu-photography-club';
if (!/^\/[a-zA-Z0-9_-]+$/.test(basePath)) throw new Error('PAGES_BASE_PATH must be a repository path.');
await mkdir(build, { recursive: true });
for (const name of ['src', 'package.json', 'package-lock.json', 'tsconfig.json', 'next-env.d.ts']) {
  await cp(path.join(source, name), path.join(build, name), { recursive: true });
}
await cp(path.join(root, 'deploy/pages'), path.join(build, 'src/preview'), { recursive: true });
await cp(path.join(root, '.pages-build/public'), path.join(build, 'public'), { recursive: true });
const modules = process.env.PAGES_NODE_MODULES || path.join(source, 'node_modules');
try { await access(path.join(build, 'node_modules')); } catch {
  await symlink(path.resolve(modules), path.join(build, 'node_modules'), process.platform === 'win32' ? 'junction' : 'dir');
}
async function put(name, text) { await writeFile(path.join(build, 'src', name), text); }
await writeFile(path.join(build, 'next.config.ts'), `export default { output: 'export', trailingSlash: true, basePath: ${JSON.stringify(basePath)}, images: { unoptimized: true }, env: { NEXT_PUBLIC_BASE_PATH: ${JSON.stringify(basePath)} } };\n`);
let layout = await readFile(path.join(source, 'src/app/layout.tsx'), 'utf8');
layout = layout.replace("export const dynamic = 'force-dynamic';", '')
  .replace('<Header site={site} />', '<Header site={site} /><div className="preview-notice" role="note">临时静态预览 · 内容均为示例；登录、投稿与报名暂未开放。</div>');
await put('app/layout.tsx', layout);
await put('lib/server-api.ts', `import { notFound } from 'next/navigation';\nimport { readPreview } from '@/preview/data';\nexport async function serverApi<T>(path: string): Promise<T> { const data = readPreview(path); if (!data) notFound(); return data as T; }\n`);
await put('lib/client-api.ts', `import { readPreview } from '@/preview/data';\nexport async function api<T>(path: string, options: RequestInit = {}): Promise<T> { if (options.method && options.method !== 'GET') throw new Error('静态预览暂未开放此功能。'); return readPreview(path) as T; }\nexport async function post<T>(_path: string, _data: unknown): Promise<T> { throw new Error('静态预览暂未开放此功能。'); }\n`);
for (const kind of ['works', 'events', 'archive', 'search']) {
  await put(`app/${kind}/page.tsx`, `import { Suspense } from 'react';\nimport { PreviewListing } from '@/preview/listing';\nexport default function Page() { return <Suspense fallback={<p>正在读取示例内容…</p>}><PreviewListing kind="${kind}" /></Suspense>; }\n`);
}
for (const [route, resource] of [['works', 'collections'], ['events', 'events'], ['archive', 'documents'], ['members', 'members']]) {
  let view = await readFile(path.join(source, `src/app/${route}/[id]/page.tsx`), 'utf8');
  view = `import { demo } from '@/preview/data';\nexport function generateStaticParams() { return demo.${resource}.map(row => ({ id: row.id })); }\n` + view;
  if (route === 'members') view = view.replace('const query = await searchParams;', 'const query: { page?: string } = {};');
  await put(`app/${route}/[id]/page.tsx`, view);
}
for (const route of ['login', 'reset-password', 'dashboard', 'dashboard/submit']) {
  await put(`app/${route}/page.tsx`, `export { default } from '@/preview/unavailable';\n`);
}
await put('app/robots.ts', `import type { MetadataRoute } from 'next';\nexport const dynamic = 'force-static';\nexport default function robots(): MetadataRoute.Robots { return { rules: { userAgent: '*', disallow: '/' } }; }\n`);
await writeFile(path.join(build, 'src/app/globals.css'), '\n.preview-notice { padding: 12px 5%; background: #eeeae2; color: #49443b; font-size: 13px; text-align: center; }\n', { flag: 'a' });
const result = spawnSync(process.execPath, [path.join(build, 'node_modules/next/dist/bin/next'), 'build', '--webpack'], { cwd: build, stdio: 'inherit', env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' } });
if (result.status !== 0) process.exit(result.status || 1);
await writeFile(path.join(build, 'out/.nojekyll'), '');
console.log(`Pages output: ${path.join(build, 'out')}`);
