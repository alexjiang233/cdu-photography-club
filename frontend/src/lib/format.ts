export function date(
  value: string,
  options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' },
) {
  return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', ...options }).format(
    new Date(value),
  );
}
