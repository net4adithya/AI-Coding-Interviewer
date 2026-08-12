import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '../services/supabase';
import { User as SupabaseUser, Session } from '@supabase/supabase-js';

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
  session: Session | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const mapSupabaseUser = (su: SupabaseUser | null): User | null => {
  if (!su) return null;
  const role = (su.user_metadata?.role?.toLowerCase() || 'intern') as Role;
  const name = su.user_metadata?.full_name || su.email?.split('@')[0] || 'Unknown';
  return {
    id: su.id,
    name,
    email: su.email || '',
    role
  };
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(async ({ data: { session: currentSession } }) => {
      setSession(currentSession);
      if (currentSession) {
        try {
          const res = await fetch(import.meta.env.VITE_API_BASE_URL + '/users/me', {
            headers: {
              'Authorization': `Bearer ${currentSession.access_token}`
            }
          });
          if (res.ok) {
            const data = await res.json();
            setUser({
              id: data.supabase_uid,
              name: currentSession.user?.user_metadata?.full_name || currentSession.user?.email?.split('@')[0] || 'Unknown',
              email: data.email,
              role: data.role as Role
            });
          } else {
            setUser(mapSupabaseUser(currentSession.user));
          }
        } catch (e) {
          setUser(mapSupabaseUser(currentSession.user));
        }
      } else {
        setUser(null);
      }
      setIsLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, currentSession) => {
      setSession(currentSession);
      if (currentSession) {
        try {
          const res = await fetch(import.meta.env.VITE_API_BASE_URL + '/users/me', {
            headers: {
              'Authorization': `Bearer ${currentSession.access_token}`
            }
          });
          if (res.ok) {
            const data = await res.json();
            setUser({
              id: data.supabase_uid,
              name: currentSession.user?.user_metadata?.full_name || currentSession.user?.email?.split('@')[0] || 'Unknown',
              email: data.email,
              role: data.role as Role
            });
          } else {
            setUser(mapSupabaseUser(currentSession.user));
          }
        } catch (e) {
          setUser(mapSupabaseUser(currentSession.user));
        }
      } else {
        setUser(null);
      }
      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password?: string) => {
    setIsLoading(true);
    let result;
    if (password) {
      result = await supabase.auth.signInWithPassword({ email, password });
    } else {
      result = await supabase.auth.signInWithOtp({ email });
    }
    const { error } = result;
    setIsLoading(false);
    if (error) {
      return { error: error.message };
    }
    return {};
  };

  const signOut = async () => {
    setIsLoading(true);
    await supabase.auth.signOut();
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signOut, session }}>
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
