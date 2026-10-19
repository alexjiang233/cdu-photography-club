import { Suspense } from 'react';
import { Dashboard } from '@/components/dashboard';
export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="loading-state">正在打开成员中心…</div>}>
      <Dashboard />
    </Suspense>
  );
}
