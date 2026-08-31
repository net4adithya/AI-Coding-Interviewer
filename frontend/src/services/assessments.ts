import api from './api';
import { demoService } from './demoApi';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export interface AssessmentCreateRequest {
  title: string;
  duration_minutes: number;
  total_questions: number;
  difficulty_distribution: Record<string, number>;
  topic_tags?: string[];
  ai_selection_enabled: boolean;
  question_ids?: number[];
  question_bank_id?: number;
}

export interface AssessmentResponse {
  id: number | string;
  title: string;
  duration_minutes: number;
  total_questions: number;
  difficulty_distribution: Record<string, number>;
  topic_tags?: string[];
  ai_selection_enabled: boolean;
  status: string;
  created_at: string;
  published_at?: string;
  assignment_id?: number | string;
}

export interface AssessmentInternResponse {
  id: number | string;
  assessment_id: number | string;
  intern_id?: number;
  intern_email?: string;
  status: string;
  assigned_at: string;
  started_at?: string;
  submitted_at?: string;
  expired_at?: string;
}

export const assessmentsService = {
  getAssessments: async (): Promise<any[]> => {
    if (DEMO_MODE) return demoService.getAssessments();
    const response = await api.get('/api/v1/assessments/');
    return response.data;
  },

  getMyAssessment: async (): Promise<any> => {
    if (DEMO_MODE) return demoService.getMyAssignment();
    const response = await api.get('/api/v1/assessments/intern/me');
    return response.data;
  },

  createAssessment: async (data: AssessmentCreateRequest): Promise<any> => {
    if (DEMO_MODE) {
      console.log('[DEMO TRACE] Routing createAssessment to demoService.confirmAssessment');
      return demoService.confirmAssessment({
        title: data.title,
        duration_minutes: data.duration_minutes,
        language: 'Python',
        topic: data.topic_tags?.[0] || 'Algorithms',
        easy_count: data.difficulty_distribution?.easy || 0,
        medium_count: data.difficulty_distribution?.medium || 0,
        hard_count: data.difficulty_distribution?.hard || 0,
        questions: [],
      });
    }
    const response = await api.post('/api/v1/assessments/', data);
    return response.data;
  },

  getAssessmentQuestions: async (assessmentId: number | string): Promise<any[]> => {
    if (DEMO_MODE) {
      const ass = await demoService.getAssessment(String(assessmentId));
      return ass?.questions || [];
    }
    const response = await api.get(`/api/v1/assessments/${assessmentId}/questions`);
    return response.data;
  },

  submitDecision: async (assignmentId: number | string, decision: string, notes?: string): Promise<any> => {
    if (DEMO_MODE) return demoService.saveDecision(String(assignmentId), decision, notes || '');
    const response = await api.post(`/api/v1/assessments/intern/${assignmentId}/decision`, {
      decision: decision,
      reviewer_notes: notes
    });
    return response.data;
  },

  getAssessment: async (id: number | string): Promise<any> => {
    if (DEMO_MODE) return demoService.getAssessment(String(id));
    const response = await api.get(`/api/v1/assessments/${id}`);
    return response.data;
  },

  previewAssessment: async (id: number | string): Promise<any[]> => {
    if (DEMO_MODE) {
      const ass = await demoService.getAssessment(String(id));
      return ass?.questions || [];
    }
    const response = await api.post(`/api/v1/assessments/${id}/preview`);
    return response.data;
  },

  generateAssessment: async (id: number | string): Promise<any> => {
    if (DEMO_MODE) return demoService.getAssessment(String(id));
    const response = await api.post(`/api/v1/assessments/${id}/generate`);
    return response.data;
  },

  publishAssessment: async (id: number | string): Promise<any> => {
    if (DEMO_MODE) return demoService.getAssessment(String(id));
    const response = await api.post(`/api/v1/assessments/${id}/publish`);
    return response.data;
  },

  assignAssessmentByEmail: async (id: number | string, email: string): Promise<any> => {
    if (DEMO_MODE) {
      console.log('[DEMO TRACE] Routing assignAssessmentByEmail to /demo/assignments/assign', { assessment_id: id, intern_email: email });
      return demoService.assignAssessment(String(id), email);
    }
    const response = await api.post(`/api/v1/assessments/${id}/assign-email`, { email });
    return response.data;
  }
};
