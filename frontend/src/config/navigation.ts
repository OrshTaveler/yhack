import type { UserRole } from '@/types';

export interface NavItem {
  to: string;
  label: string;
  end?: boolean;
}

export const NAV_BY_ROLE: Record<UserRole, NavItem[]> = {
  director: [
    { to: '/director', label: 'Обзор', end: true },
    { to: '/director/schedule-generator', label: 'Генерация расписания' },
    { to: '/director/assignments', label: 'Назначение классов' },
    { to: '/director/schedules', label: 'Расписания' },
    { to: '/director/lesson-stats', label: 'Статистика уроков' },
  ],
  teacher: [
    { to: '/teacher', label: 'Обзор', end: true },
    { to: '/teacher/homework', label: 'Проверка работ' },
    { to: '/teacher/noise', label: 'Анализ шума' },
    { to: '/teacher/statistics', label: 'Статистика классов' },
    { to: '/schedule', label: 'Расписание' },
  ],
  student: [
    { to: '/student', label: 'Обзор', end: true },
    { to: '/student/homework', label: 'Домашние задания' },
    { to: '/student/grades', label: 'Мои оценки' },
    { to: '/schedule', label: 'Расписание' },
  ],
};

export function homePathForRole(role: UserRole): string {
  const map: Record<UserRole, string> = {
    director: '/director',
    teacher: '/teacher',
    student: '/student',
  };
  return map[role];
}
