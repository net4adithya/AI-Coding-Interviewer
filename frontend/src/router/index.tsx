import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Layouts
import { AuthorityLayout } from '@/layouts/AuthorityLayout';
import { InternLayout } from '@/layouts/InternLayout';

// Auth Pages
import { Login } from '@/pages/auth/Login';

// Authority Pages
import { Dashboard } from '@/pages/authority/Dashboard';
import { QuestionBank } from '@/pages/authority/QuestionBank';
import { QuestionBankDetails } from '@/pages/authority/QuestionBankDetails';
import { Interviews } from '@/pages/authority/Interviews';
import { CreateInterview } from '@/pages/authority/CreateInterview';
import { ReviewInterview } from '@/pages/authority/ReviewInterview';
import { Candidates } from '@/pages/authority/Candidates';
import { Submissions } from '@/pages/authority/Submissions';

// Intern Pages
import { InterviewOverview } from '@/pages/intern/InterviewOverview';
import { Workspace } from '@/pages/intern/Workspace';
import { Completed } from '@/pages/intern/Completed';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  
  // Authority Routes
  {
    path: '/authority',
    element: (
      <ProtectedRoute allowedRole="authority">
        <AuthorityLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: '',
        element: <Navigate to="/authority/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'question-bank',
        element: <QuestionBank />,
      },
      {
        path: 'question-bank/:id',
        element: <QuestionBankDetails />,
      },
      {
        path: 'interviews',
        element: <Interviews />,
      },
      {
        path: 'interviews/new',
        element: <CreateInterview />,
      },
      {
        path: 'interviews/:id/review',
        element: <ReviewInterview />,
      },
      {
        path: 'candidates',
        element: <Candidates />,
      },
      {
        path: 'submissions',
        element: <Submissions />,
      }
    ],
  },
  
  // Intern Routes
  {
    path: '/intern/interview',
    element: (
      <ProtectedRoute allowedRole="intern">
        <InternLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: '',
        element: <Navigate to="/intern/interview/overview" replace />,
      },
      {
        path: 'overview',
        element: <InterviewOverview />,
      },
      {
        path: 'workspace',
        element: <Workspace />,
      },
      {
        path: 'completed',
        element: <Completed />,
      },
    ],
  },
]);

export default router;
