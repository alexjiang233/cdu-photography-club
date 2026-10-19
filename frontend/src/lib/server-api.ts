import 'server-only';
import { cookies, headers } from 'next/headers';
import { notFound } from 'next/navigation';

export async function serverApi<T>(path: string): Promise<T> {
  const cookieStore = await cookies();
  const incoming = await headers();
  const forwardedFor = incoming.get('x-forwarded-for');
  const response = await fetch(
    `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/${path}`,
    {
      headers: {
        Cookie: cookieStore.toString(),
        ...(forwardedFor ? { 'X-Forwarded-For': forwardedFor } : {}),
      },
      cache: 'no-store',
      signal: AbortSignal.timeout(10000),
    },
  );
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error(`内容服务暂不可用（${response.status}）。请稍后重试。`);
  return response.json();
}
