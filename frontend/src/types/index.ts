export type UserRole = 'teacher' | 'student';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

export interface ClassGroup {
  id: string;
  name: string;
  grade: number;
}

export interface Subject {
  id: string;
  name: string;
  hoursPerWeek: number;
}

export interface ScheduleSlot {
  id: string;
  dayOfWeek: number;
  period: number;
  subjectId: string;
  classId: string;
  teacherId?: string;
  room?: string;
}

export interface HomeworkSubmission {
  id: string;
  studentId: string;
  studentName: string;
  classId: string;
  subjectId: string;
  subjectName: string;
  photoUrl: string;
  submittedAt: string;
  aiGrade?: number;
  aiComment?: string;
  teacherGrade?: number;
  status: 'pending' | 'ai_reviewed' | 'teacher_reviewed';
}

export interface NoiseSample {
  timestamp: string;
  levelDb: number;
}

export interface StudentNoiseStat {
  studentId: string;
  studentName: string;
  avgLevelDb: number;
  peakLevelDb: number;
  incidentsCount: number;
}

export interface LessonNoiseReport {
  id: string;
  lessonId: string;
  classId: string;
  className: string;
  subjectName: string;
  startedAt: string;
  endedAt?: string;
  samples: NoiseSample[];
  topNoisyStudents: StudentNoiseStat[];
  summary?: string;
  status: 'recording' | 'processing' | 'ready';
}

export interface StudentGradeStat {
  studentId: string;
  studentName: string;
  subjectId: string;
  subjectName: string;
  averageGrade: number;
  worksCount: number;
}

export interface ClassOverview {
  classId: string;
  className: string;
  studentsCount: number;
  averageGrade: number;
  pendingHomeworks: number;
}
