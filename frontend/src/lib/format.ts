export function date(
  value: string,
  options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' },
) {
  return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', ...options }).format(
    new Date(value),
  );
}
export function size(value: number) {
  return value < 1024 * 1024
    ? `${(value / 1024).toFixed(1)} KB`
    : `${(value / 1024 / 1024).toFixed(1)} MB`;
}
export const statusLabel: Record<string, string> = {
  draft: '草稿',
  pending: '待审核',
  published: '已发布',
  returned: '退回修改',
  archived: '已归档',
};
export const categories: Record<string, string> = {
  tutorial: '摄影教程',
  publication: '刊物与展览',
  planning: '活动策划',
  handover: '换届交接',
  other: '其他资料',
};
