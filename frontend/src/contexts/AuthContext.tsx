// frontend/src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Role = 'authority' | 'intern';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signIn: (email: string, password?: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  demoToken: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STORAGE_KEY_USER = 'demo_user';
const STORAGE_KEY_TOKEN = 'demo_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [demoToken, setDemoToken] = useState<string | null>(null);

  // ── Restore session from localStorage on mount ────────────────────────────
  useEffect(() => {
    if (DEMO_MODE) {
      const storedUser = localStorage.getItem(STORAGE_KEY_USER);
      const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
      if (storedUser && storedToken) {
        try {
          setUser(JSON.parse(storedUser));
          setDemoToken(storedToken);
        } catch {
          localStorage.removeItem(STORAGE_KEY_USER);
          localStorage.removeItem(STORAGE_KEY_TOKEN);
        }
      }
      setIsLoading(false);
      return;
    }

    // ── Production: Supabase auth ───────────────────────────────────────────
    (async () => {
      try {
        const { supabase } = await import('../services/supabase');
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        if (currentSession) {
          try {
            const res = await fetch(API_BASE + '/users/me', {
              headers: { 'Authorization': `Bearer ${currentSession.access_token}` }
            });
            if (res.ok) {
              const data = await res.json();
              setUser({
                id: data.supabase_uid,
                name: currentSession.user?.user_metadata?.full_name || currentSession.user?.email?.split('@')[0] || 'Unknown',
                email: data.email,
                role: data.role as Role,
              });
            } else {
              const su = currentSession.user;
              setUser({
                id: su.id,
                name: su.user_metadata?.full_name || su.email?.split('@')[0] || 'Unknown',
                email: su.email || '',
                role: (su.user_metadata?.role?.toLowerCase() || 'intern') as Role,
              });
            }
          } catch {
            const su = currentSession.user;
            setUser({
              id: su.id,
              name: su.user_metadata?.full_name || su.email?.split('@')[0] || 'Unknown',
              email: su.email || '',
              role: (su.user_metadata?.role?.toLowerCase() || 'intern') as Role,
            });
          }
        }
      } catch (e) {
        console.warn('[AuthContext] Supabase init failed:', e);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // ── signIn ────────────────────────────────────────────────────────────────
  const signIn = async (email: string, password?: string): Promise<{ error?: string }> => {
    setIsLoading(true);
    try {
      if (DEMO_MODE) {
        // Call the demo login endpoint
        const res = await fetch(`${API_BASE}/demo/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password: password || '' }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Login failed' }));
          return { error: err.detail || 'Invalid credentials' };
        }
        const data = await res.json();
        const u: User = {
          id: email,
          name: data.name,
          email: data.email,
          role: data.role as Role,
        };
        setUser(u);
        setDemoToken(data.token);
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
        localStorage.setItem(STORAGE_KEY_TOKEN, data.token);
        return {};
      }

      // Production Supabase login
      const { supabase } = await import('../services/supabase');
      let result;
      if (password) {
        result = await supabase.auth.signInWithPassword({ email, password });
      } else {
        result = await supabase.auth.signInWithOtp({ email });
      }
      if (result.error) {
        return { error: result.error.message };
      }
      return {};
    } finally {
      setIsLoading(false);
    }
  };

  // ── signOut ───────────────────────────────────────────────────────────────
  const signOut = async () => {
    setIsLoading(true);
    if (DEMO_MODE) {
      setUser(null);
      setDemoToken(null);
      localStorage.removeItem(STORAGE_KEY_USER);
      localStorage.removeItem(STORAGE_KEY_TOKEN);
    } else {
      try {
        const { supabase } = await import('../services/supabase');
        await supabase.auth.signOut();
      } catch {
        // ignore
      }
      setUser(null);
    }
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signOut, demoToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
