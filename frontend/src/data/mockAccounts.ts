import type { User, UserRole } from '@/types';

export interface MockAccount {
  email: string;
  password: string;
  user: User;
}

/** Тестовые учётные записи (до подключения JWT на бэкенде) */
export const MOCK_ACCOUNTS: MockAccount[] = [
  {
    email: 'teacher@school.ru',
    password: 'teacher123',
    user: {
      id: 'tch-1',
      name: 'Петров И.В.',
      email: 'teacher@school.ru',
      role: 'teacher',
    },
  },
  {
    email: 'student@school.ru',
    password: 'student123',
    user: {
      id: 'std-1',
      name: 'Сидоров М.А.',
      email: 'student@school.ru',
      role: 'student',
    },
  },
];

export const ROLE_LABELS: Record<UserRole, string> = {
  teacher: 'Учитель',
  student: 'Ученик',
};
