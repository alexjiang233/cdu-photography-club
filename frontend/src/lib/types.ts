export type Profile = {
  id: string;
  display_name: string;
  bio: string;
  cohort: string;
  is_public: boolean;
  is_demo: boolean;
};
export type Identity = {
  authenticated: boolean;
  username?: string;
  member?: boolean;
  staff?: boolean;
  profile?: Profile | null;
  can_edit_events?: boolean;
  can_edit_documents?: boolean;
  can_review?: boolean;
};
export type Photo = {
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
  editable: boolean;
  review_note: string;
  event?: string | null;
};
export type Collection = Editorial & {
  author: Profile;
  photos: Photo[];
  featured: boolean;
  published_at: string | null;
};
export type ClubEvent = Editorial & {
  starts_at: string;
  ends_at: string;
  registration_deadline: string;
  location: string;
  capacity: number;
  registration_count: number;
  registration_open: boolean;
  my_registration: boolean;
  cover_url: string | null;
};
export type DocumentVersion = {
  id: string;
  version: number;
  note: string;
  filename: string;
  size: number;
  download_url: string;
  created_at: string;
};
export type ArchiveDocument = Editorial & {
  year: number;
  category: string;
  versions: DocumentVersion[];
  updated_at: string;
};
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type Site = {
  name: string;
  introduction: string;
  join_instructions: string;
  contact_email: string;
  logo_url: string | null;
  has_demo: boolean;
  tags: string[];
};
export type Asset = {
  id: string;
  state: string;
  error: string;
  original_name: string;
  size: number;
  thumbnail_url?: string | null;
};
export type Discussion = {
  id: string;
  text: string;
  author_name: string;
  approved: boolean;
  created_at: string;
};
export type Dashboard = {
  identity: Identity;
  collections: Collection[];
  registrations: {
    id: string;
    event_id: string;
    title: string;
    starts_at: string;
    cancelled: boolean;
  }[];
  notices: { id: string; text: string; href: string; read: boolean; created_at: string }[];
};
