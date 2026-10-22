import type { Photo } from '@/lib/types';
export function PhotoFacts({ photo, compact = false }: { photo: Photo; compact?: boolean }) {
  const info = photo.shooting || {};
  const rows = [
    ['摄影', info.photographer || '未署名'],
    ['拍摄时间', info.taken_at || '未记录'],
    ['机身', info.camera_body || '未记录'],
    ['镜头', info.lens || '未记录'],
    ['快门', info.shutter_speed || '—'],
    ['光圈', info.aperture || '—'],
    ['ISO', info.iso || '—'],
  ];
  return (
    <div className={`photo-facts${compact ? ' photo-facts-compact' : ''}`}>
      <dl>
        {rows.map(([name, value]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {!compact && info.taken_at && info.time_source === 'exif' && (
        <small>时间来自相机 EXIF，未校正相机时钟。</small>
      )}
    </div>
  );
}
