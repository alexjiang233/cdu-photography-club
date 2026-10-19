import type { Metadata } from 'next';

export const metadata: Metadata = { title: '成员中心', robots: { index: false, follow: false } };
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
