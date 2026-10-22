export type Profile = {
  id: string;
  display_name: string;
  bio: string;
  cohort: string;
  is_public: boolean;
  is_demo: boolean;
};
export type Photo = {
  shooting?: {
    photographer?: string;
    taken_at?: string;
    time_source?: string;
    camera_body?: string;
    lens?: string;
    shutter_speed?: string;
    aperture?: string;
    iso?: string;
    focal_length?: string;
  };
  id: string;
  asset_id: string;
  caption: string;
  position: number;
  display_url: string | null;
  thumbnail_url: string | null;
  width: number | null;
  height: number | null;
};
export type Editorial = {
  id: string;
  title: string;
  description: string;
  tags: string[];
  status: string;
  visibility: string;
  is_demo: boolean;
  review_note: string;
  event?: string | null;
};
export type Collection = Editorial & {
  is_placeholder?: boolean;
  code: string;
  author: Profile;
  photos: Photo[];
  featured: boolean;
  published_at: string | null;
};
export type ClubEvent = Editorial & {
  photos?: Photo[];
  starts_at: string;
  ends_at: string;
  registration_deadline: string;
  location: string;
  capacity: number;
  registration_count: number;
  cover_url: string | null;
};
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type Site = {
  contact_qr_url?: string | null;
  name: string;
  introduction: string;
  join_instructions: string;
  contact_email: string;
  logo_url: string | null;
  has_demo: boolean;
  tags: string[];
  stats: {
    collections: number;
    photos: number;
    events: number;
    documents: number;
    members: number;
  };
};
