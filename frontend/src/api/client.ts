const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
  },
  schedule: {
    getMy: () => request<unknown>('/schedule/me'),
    getForUser: (userId: string) => request<unknown>(`/schedule/user/${userId}`),
    generate: (payload: unknown) =>
      request<unknown>('/schedule/generate', { method: 'POST', body: JSON.stringify(payload) }),
  },
  homework: {
    listForTeacher: () => request<unknown>('/homework/teacher'),
    upload: (formData: FormData) =>
      fetch(`${API_BASE}/homework/upload`, { method: 'POST', body: formData }),
    confirmGrade: (id: string, grade: number) =>
      request<unknown>(`/homework/${id}/grade`, {
        method: 'PATCH',
        body: JSON.stringify({ grade }),
      }),
  },
  noise: {
    startSession: (lessonId: string) =>
      request<unknown>('/noise/sessions', { method: 'POST', body: JSON.stringify({ lessonId }) }),
    stopSession: (sessionId: string) =>
      request<unknown>(`/noise/sessions/${sessionId}/stop`, { method: 'POST' }),
    getReport: (sessionId: string) => request<unknown>(`/noise/sessions/${sessionId}/report`),
    listLessonStats: () => request<unknown>('/noise/lessons'),
  },
  classes: {
    list: () => request<unknown>('/classes'),
    assignTeacher: (classId: string, teacherId: string) =>
      request<unknown>(`/classes/${classId}/teacher`, {
        method: 'PUT',
        body: JSON.stringify({ teacherId }),
      }),
  },
  stats: {
    teacherOverview: () => request<unknown>('/stats/teacher'),
    studentGrades: (classId: string) => request<unknown>(`/stats/class/${classId}/grades`),
  },
};
