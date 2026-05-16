import type {
  ClassDto,
  HomeworkDto,
  NoiseSessionDto,
  ScheduleGeneratePayload,
  ScheduleSlotDto,
  StudentGradeDto,
  SubjectDto,
  TeacherStatsDto,
  UserDto,
} from './types';

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
  const headers: Record<string, string> = {};
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
    getMy: () => request<{ slots: ScheduleSlotDto[] }>('/schedule/me'),
    getForUser: (userId: string) =>
      request<{ slots: ScheduleSlotDto[] }>(`/schedule/user/${userId}`),
    generate: (payload: ScheduleGeneratePayload) =>
      request<{ slots: ScheduleSlotDto[] }>('/schedule/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  homework: {
    listForTeacher: () => request<{ items: HomeworkDto[] }>('/homework/teacher'),
    listMy: () => request<{ items: HomeworkDto[] }>('/homework/my'),
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
        return res.json() as Promise<HomeworkDto>;
      });
    },
    confirmGrade: (id: string, grade: number) =>
      request<HomeworkDto>(`/homework/${id}/grade`, {
        method: 'PATCH',
        body: JSON.stringify({ grade }),
      }),
  },
  noise: {
    startSession: (classId: string, subjectId: string) =>
      request<NoiseSessionDto>('/noise/sessions', {
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
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error((err as { detail?: string }).detail ?? `Stop failed: ${res.status}`);
        }
        return res.json() as Promise<NoiseSessionDto>;
      });
    },
    getReport: (sessionId: string) =>
      request<NoiseSessionDto>(`/noise/sessions/${sessionId}/report`),
    listLessonStats: () => request<{ items: NoiseSessionDto[] }>('/noise/lessons'),
  },
  classes: {
    list: () => request<{ items: ClassDto[] }>('/classes'),
    assignTeacher: (classId: string, teacherId: string) =>
      request<ClassDto>(`/classes/${classId}/teacher`, {
        method: 'PUT',
        body: JSON.stringify({ teacher_id: teacherId }),
      }),
  },
  subjects: {
    list: () => request<{ items: SubjectDto[] }>('/subjects'),
  },
  users: {
    list: (role?: 'teacher' | 'student') =>
      request<{ items: UserDto[] }>(role ? `/users?role=${role}` : '/users'),
  },
  stats: {
    teacherOverview: () => request<TeacherStatsDto>('/stats/teacher'),
    studentGrades: (classId: string) =>
      request<{ items: StudentGradeDto[] }>(`/stats/class/${classId}/grades`),
  },
};
