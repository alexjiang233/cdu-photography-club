import Link from 'next/link';
import type { Collection } from '@/lib/types';
export function AlbumCard({ album }: { album: Collection }) {
  const photo = album.photos.find((p) => p.display_url);
  return (
    <article className="gl-album" data-reveal="gallery-print" data-scroll-reveal>
      <Link href={`/works/${album.id}`}>
        <div className="gl-album-photo">
          {photo?.display_url && (
            <img
              src={photo.display_url}
              alt={photo.caption || album.title}
              width={photo.width || 1200}
              height={photo.height || 800}
              loading="lazy"
            />
          )}
        </div>
        <div className="gl-album-title">
          <h3>{album.title}</h3>
        </div>
      </Link>
      <p>{album.description}</p>
    </article>
  );
}
