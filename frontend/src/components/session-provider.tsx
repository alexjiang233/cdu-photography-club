'use client';
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/client-api';
import type { Identity } from '@/lib/types';
const SessionContext = createContext<{
  user: Identity;
  loading: boolean;
  refresh: () => Promise<void>;
}>({ user: { authenticated: false }, loading: true, refresh: async () => {} });
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Identity>({ authenticated: false });
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try {
      setUser(await api<Identity>('auth/session/'));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    refresh().catch(() => setLoading(false));
  }, [refresh]);
  return (
    <SessionContext.Provider value={{ user, loading, refresh }}>{children}</SessionContext.Provider>
  );
}
export const useSession = () => useContext(SessionContext);
