import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { RoleGuard } from '@/components/common/RoleGuard';
import { RequireAuth } from '@/components/common/RequireAuth';
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthPage } from '@/pages/AuthPage';
import { SchedulePage } from '@/pages/shared/SchedulePage';
import { TeacherDashboard } from '@/pages/teacher/TeacherDashboard';
import { HomeworkReviewPage } from '@/pages/teacher/HomeworkReviewPage';
import { ClassroomNoisePage } from '@/pages/teacher/ClassroomNoisePage';
import { ClassStatisticsPage } from '@/pages/teacher/ClassStatisticsPage';
import { StudentDashboard } from '@/pages/student/StudentDashboard';
import { HomeworkUploadPage } from '@/pages/student/HomeworkUploadPage';
import { MyGradesPage } from '@/pages/student/MyGradesPage';
import { StudentProfilePage } from '@/pages/student/StudentProfilePage';

function HomeRedirect() {
  return <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage />} />
          <Route path="/" element={<HomeRedirect />} />

          <Route element={<RequireAuth />}>
            <Route element={<AppLayout />}>
              <Route element={<RoleGuard allowed={['teacher', 'student']} />}>
                <Route path="/schedule" element={<SchedulePage />} />
              </Route>

              <Route element={<RoleGuard allowed={['teacher']} />}>
                <Route path="/teacher" element={<TeacherDashboard />} />
                <Route path="/teacher/homework" element={<HomeworkReviewPage />} />
                <Route path="/teacher/noise" element={<ClassroomNoisePage />} />
                <Route path="/teacher/statistics" element={<ClassStatisticsPage />} />
              </Route>

              <Route element={<RoleGuard allowed={['student']} />}>
                <Route path="/student" element={<StudentDashboard />} />
                <Route path="/student/profile" element={<StudentProfilePage />} />
                <Route path="/student/homework" element={<HomeworkUploadPage />} />
                <Route path="/student/grades" element={<MyGradesPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
