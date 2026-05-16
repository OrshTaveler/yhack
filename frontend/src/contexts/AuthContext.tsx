import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, getStoredToken, setStoredToken } from '@/api/client';
import type { User, UserRole } from '@/types';

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function mapUser(u: { id: string; name: string; email: string; role: UserRole }): User {
  return { id: u.id, name: u.name, email: u.email, role: u.role };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api.auth
      .me()
      .then((u) => setUser(mapUser(u)))
      .catch(() => setStoredToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.auth.login(email, password);
    setStoredToken(res.access_token);
    setUser(mapUser(res.user));
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const res = await api.auth.register({
      name: input.name,
      email: input.email,
      password: input.password,
      role: input.role,
    });
    setStoredToken(res.access_token);
    setUser(mapUser(res.user));
  }, []);

  const logout = useCallback(() => {
    setStoredToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
