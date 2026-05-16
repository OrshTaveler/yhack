/** Извлекает параллель из названия класса: «5А» → 5, «10Б» → 10 */
export function parseGradeFromClassName(name: string): number | null {
  const match = name.trim().match(/^(\d+)/);
  if (!match) return null;
  const grade = Number(match[1]);
  if (grade < 1 || grade > 11) return null;
  return grade;
}

export const STUDENTS_COUNT_MIN = 5;
export const STUDENTS_COUNT_MAX = 30;
