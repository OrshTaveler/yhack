import {
  createContext,
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { MOCK_ACCOUNTS, type MockAccount } from '@/data/mockAccounts';
import type { User, UserRole } from '@/types';

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function findAccount(
  email: string,
  password: string,
  extra: MockAccount[],
): MockAccount | undefined {
  const normalized = email.trim().toLowerCase();
  return [...MOCK_ACCOUNTS, ...extra].find(
    (a) => a.email.toLowerCase() === normalized && a.password === password,
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [registeredAccounts, setRegisteredAccounts] = useState<MockAccount[]>([]);

  const login = useCallback(
    async (email: string, password: string) => {
      const account = findAccount(email, password, registeredAccounts);
      if (!account) {
        throw new Error('Неверный email или пароль');
      }
      setUser(account.user);
    },
    [registeredAccounts],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const email = input.email.trim().toLowerCase();
      const exists = [...MOCK_ACCOUNTS, ...registeredAccounts].some(
        (a) => a.email.toLowerCase() === email,
      );
      if (exists) {
        throw new Error('Пользователь с таким email уже существует');
      }

      const newUser: User = {
        id: `usr-${Date.now()}`,
        name: input.name.trim(),
        email,
        role: input.role,
      };

      const account: MockAccount = {
        email,
        password: input.password,
        user: newUser,
      };

      setRegisteredAccounts((prev) => [...prev, account]);
      setUser(newUser);
    },
    [registeredAccounts],
  );

  const logout = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({ user, login, register, logout }),
    [user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
