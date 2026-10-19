function message(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(message).join('；');
  if (value && typeof value === 'object') return Object.values(value).map(message).join('；');
  return '操作未完成，请稍后重试。';
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET') {
    let token = document.cookie
      .split('; ')
      .find((c) => c.startsWith('csrftoken='))
      ?.split('=')[1];
    if (!token) {
      const session = await fetch('/api/auth/session/', {
        credentials: 'same-origin',
        cache: 'no-store',
      }).then((r) => r.json());
      token = session.csrf_token;
    }
    if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
    if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`/api/${path}`, {
    ...options,
    headers,
    credentials: 'same-origin',
    cache: 'no-store',
  });
  const data = await response.json().catch(() => ({ detail: '服务暂不可用，请稍后重试。' }));
  if (!response.ok) throw new Error(message(data));
  return data as T;
}
export function post<T>(path: string, data: unknown) {
  return api<T>(path, { method: 'POST', body: JSON.stringify(data) });
}
