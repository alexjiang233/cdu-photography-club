import { Suspense } from 'react';
import { WorkEditor } from '@/components/work-editor';
export default function Submit() {
  return (
    <Suspense fallback={<div className="loading-state">正在打开作品编辑器…</div>}>
      <WorkEditor />
    </Suspense>
  );
}
