// frontend/src/services/demoApi.ts
/**
 * Axios instance for DEMO MODE API calls.
 * 
 * - Uses /demo/* prefix
 * - Attaches X-Demo-Token header from localStorage
 * - Never calls Supabase
 */

import axios from 'axios';

const STORAGE_KEY_TOKEN = 'demo_token';

const demoApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

demoApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_KEY_TOKEN);
  if (token) {
    config.headers['X-Demo-Token'] = token;
  }
  return config;
});

demoApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Surface the actual backend error detail instead of hiding it
    const detail = error.response?.data?.detail || error.message;
    if (error.response?.status === 401) {
      // Clear stale demo session
      localStorage.removeItem('demo_user');
      localStorage.removeItem('demo_token');
      window.location.href = '/login';
    }
    const enhanced = new Error(detail);
    (enhanced as any).response = error.response;
    return Promise.reject(enhanced);
  }
);

export default demoApi;

// ── Typed API calls ──────────────────────────────────────────────────────────

export const demoService = {
  // Dashboard
  getDashboardStats: () => demoApi.get('/demo/dashboard/stats').then(r => r.data),

  // Question Banks
  getQuestionBanks: () => demoApi.get('/demo/question-banks').then(r => r.data),
  getQuestionBank: (id: string | number) => demoApi.get(`/demo/question-banks/${id}`).then(r => r.data),
  uploadQuestionBank: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return demoApi.post('/demo/question-banks/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data);
  },

  // Assessment selection review
  reviewSelection: (data: {
    title: string;
    description?: string;
    duration_minutes: number;
    language: string;
    topic: string;
    selected_questions: any[];
  }) => demoApi.post('/demo/assessments/review-selection', data).then(r => r.data),

  // Assessment generation
  generateQuestions: (data: {
    title: string;
    description?: string;
    duration_minutes: number;
    language: string;
    topic: string;
    easy_count: number;
    medium_count: number;
    hard_count: number;
  }) => demoApi.post('/demo/assessments/generate', data).then(r => r.data),

  confirmAssessment: (data: {
    title: string;
    description?: string;
    duration_minutes: number;
    language: string;
    topic: string;
    easy_count: number;
    medium_count: number;
    hard_count: number;
    questions: any[];
  }) => demoApi.post('/demo/assessments/confirm', data).then(r => r.data),

  getAssessments: () => demoApi.get('/demo/assessments').then(r => r.data),
  getAssessment: (id: string) => demoApi.get(`/demo/assessments/${id}`).then(r => r.data),

  // Candidates
  getCandidates: () => demoApi.get('/demo/candidates').then(r => r.data),

  // Assignments
  assignAssessment: (assessment_id: string, intern_email: string) =>
    demoApi.post('/demo/assignments/assign', { assessment_id, intern_email }).then(r => r.data),
  getMyAssignment: () => demoApi.get('/demo/assignments/me').then(r => r.data),
  startAssignment: () => demoApi.post('/demo/assignments/start').then(r => r.data),

  // Code execution
  runCode: (source_code: string, language: string, stdin: string) =>
    demoApi.post('/demo/execute/run', { source_code, language, stdin }).then(r => r.data),
  runTestCases: (source_code: string, language: string, test_cases: any[]) =>
    demoApi.post('/demo/execute/test-cases', { source_code, language, test_cases }).then(r => r.data),

  // Submissions
  submitAssessment: (data: {
    assessment_id: string;
    code_by_question: Record<string, { language: string; code: string }>;
    final_language: string;
  }) => demoApi.post('/demo/submissions/submit', data).then(r => r.data),

  getSubmissions: () => demoApi.get('/demo/submissions').then(r => r.data),
  getSubmissionDetail: (id: string) => demoApi.get(`/demo/submissions/${id}`).then(r => r.data),
  getReviewStatus: (id: string) => demoApi.get(`/demo/submissions/${id}/review-status`).then(r => r.data),

  // Authority decision
  saveDecision: (submissionId: string, decision: string, notes: string = '') =>
    demoApi.post(`/demo/submissions/${submissionId}/decision`, { decision, notes }).then(r => r.data),
  getDecision: (submissionId: string) =>
    demoApi.get(`/demo/submissions/${submissionId}/decision`).then(r => r.data),

  // Reset
  resetDemo: () => demoApi.post('/demo/reset').then(r => r.data),
};
