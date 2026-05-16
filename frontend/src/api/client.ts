const API_BASE = import.meta.env.VITE_API_URL ?? '/api';
const TOKEN_KEY = 'access_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
  };
  if (!(options?.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string>) },
  });

  if (!response.ok) {
    let detail = `API error: ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string | { msg: string }[] };
      if (typeof body.detail === 'string') {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail.map((d) => d.msg).join(', ');
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: 'director' | 'teacher' | 'student';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    register: (data: {
      name: string;
      email: string;
      password: string;
      role: AuthUser['role'];
    }) =>
      request<TokenResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    me: () => request<AuthUser>('/auth/me'),
  },
  schedule: {
    getMy: () => request<{ slots: unknown[] }>('/schedule/me'),
    getForUser: (userId: string) => request<{ slots: unknown[] }>(`/schedule/user/${userId}`),
    generate: (payload: unknown) =>
      request<{ slots: unknown[] }>('/schedule/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  homework: {
    listForTeacher: () => request<{ items: unknown[] }>('/homework/teacher'),
    listMy: () => request<{ items: unknown[] }>('/homework/my'),
    upload: (formData: FormData) => {
      const token = getStoredToken();
      return fetch(`${API_BASE}/homework/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error((err as { detail?: string }).detail ?? `Upload failed: ${res.status}`);
        }
        return res.json();
      });
    },
    confirmGrade: (id: string, grade: number) =>
      request<unknown>(`/homework/${id}/grade`, {
        method: 'PATCH',
        body: JSON.stringify({ grade }),
      }),
  },
  noise: {
    startSession: (classId: string, subjectId: string) =>
      request<unknown>('/noise/sessions', {
        method: 'POST',
        body: JSON.stringify({ class_id: classId, subject_id: subjectId }),
      }),
    stopSession: (sessionId: string, audio?: Blob) => {
      const token = getStoredToken();
      const form = new FormData();
      if (audio) {
        form.append('audio', audio, 'lesson.webm');
      }
      return fetch(`${API_BASE}/noise/sessions/${sessionId}/stop`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      }).then(async (res) => {
        if (!res.ok) throw new Error(`Stop failed: ${res.status}`);
        return res.json();
      });
    },
    getReport: (sessionId: string) => request<unknown>(`/noise/sessions/${sessionId}/report`),
    listLessonStats: () => request<{ items: unknown[] }>('/noise/lessons'),
  },
  classes: {
    list: () => request<{ items: unknown[] }>('/classes'),
    assignTeacher: (classId: string, teacherId: string) =>
      request<unknown>(`/classes/${classId}/teacher`, {
        method: 'PUT',
        body: JSON.stringify({ teacher_id: teacherId }),
      }),
  },
  stats: {
    teacherOverview: () => request<unknown>('/stats/teacher'),
    studentGrades: (classId: string) => request<unknown>(`/stats/class/${classId}/grades`),
  },
};
