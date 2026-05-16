export interface ScheduleSlotDto {
  id: string;
  day_of_week: number;
  period: number;
  subject_id: string;
  subject_name: string;
  class_id: string;
  class_name: string;
  teacher_id?: string | null;
  room?: string | null;
}

export interface HomeworkDto {
  id: string;
  student_id: string;
  student_name: string;
  class_id: string;
  subject_id: string;
  subject_name: string;
  photo_url: string;
  submitted_at: string;
  ai_grade?: number | null;
  ai_comment?: string | null;
  teacher_grade?: number | null;
  status: 'pending' | 'ai_reviewed' | 'teacher_reviewed';
}

export interface ClassDto {
  id: string;
  name: string;
  grade: number;
  students_count: number;
  teacher_id?: string | null;
  teacher_name?: string | null;
}

export interface SubjectDto {
  id: string;
  name: string;
}

export interface UserDto {
  id: string;
  name: string;
  email: string;
  role: 'director' | 'teacher' | 'student';
}

export interface NoiseSessionDto {
  id: string;
  lesson_id: string;
  class_id: string;
  class_name: string;
  subject_name: string;
  started_at: string;
  ended_at?: string | null;
  samples: { timestamp: string; level_db: number }[];
  top_noisy_students: {
    student_id: string;
    student_name: string;
    avg_level_db: number;
    peak_level_db: number;
    incidents_count: number;
  }[];
  summary?: string | null;
  status: 'recording' | 'processing' | 'ready';
}

export interface TeacherStatsDto {
  pending_homeworks: number;
  classes_count: number;
  average_grade: number;
  classes: {
    class_id: string;
    class_name: string;
    students_count: number;
    average_grade: number;
    pending_homeworks: number;
  }[];
}

export interface StudentGradeDto {
  student_id: string;
  student_name: string;
  subject_id: string;
  subject_name: string;
  average_grade: number;
  works_count: number;
}

export interface ScheduleGeneratePayload {
  classes: { name: string; students_count: number }[];
  subjects: { subject_name: string; hours_per_week: number }[];
  periods_per_day?: number;
  days_per_week?: number;
}
