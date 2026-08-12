import api from './api';

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
  id: number;
  title: string;
  duration_minutes: number;
  total_questions: number;
  difficulty_distribution: Record<string, number>;
  topic_tags?: string[];
  ai_selection_enabled: boolean;
  status: string;
  created_at: string;
  published_at?: string;
  assignment_id?: number;
}

export interface AssessmentInternResponse {
  id: number;
  assessment_id: number;
  intern_id: number;
  status: string;
  assigned_at: string;
  started_at?: string;
  submitted_at?: string;
  expired_at?: string;
}

export const assessmentsService = {
  getAssessments: async (): Promise<AssessmentResponse[]> => {
    const response = await api.get('/api/v1/assessments/');
    return response.data;
  },

  getMyAssessment: async (): Promise<AssessmentResponse> => {
    const response = await api.get('/api/v1/assessments/intern/me');
    return response.data;
  },

  createAssessment: async (data: AssessmentCreateRequest): Promise<AssessmentResponse> => {
    const response = await api.post('/api/v1/assessments/', data);
    return response.data;
  },

  getAssessmentQuestions: async (assessmentId: number): Promise<any[]> => {
    const response = await api.get(`/api/v1/assessments/${assessmentId}/questions`);
    return response.data;
  },

  submitDecision: async (assignmentId: number, decision: string, notes?: string): Promise<any> => {
    const response = await api.post(`/api/v1/assessments/intern/${assignmentId}/decision`, {
      decision: decision,
      reviewer_notes: notes
    });
    return response.data;
  },

  getAssessment: async (id: number): Promise<AssessmentResponse> => {
    const response = await api.get(`/api/v1/assessments/${id}`);
    return response.data;
  },

  previewAssessment: async (id: number): Promise<any[]> => {
    const response = await api.post(`/api/v1/assessments/${id}/preview`);
    return response.data;
  },

  generateAssessment: async (id: number): Promise<AssessmentResponse> => {
    const response = await api.post(`/api/v1/assessments/${id}/generate`);
    return response.data;
  },

  publishAssessment: async (id: number): Promise<AssessmentResponse> => {
    const response = await api.post(`/api/v1/assessments/${id}/publish`);
    return response.data;
  },

  assignAssessmentByEmail: async (id: number, email: string): Promise<AssessmentInternResponse> => {
    const response = await api.post(`/api/v1/assessments/${id}/assign-email`, { email });
    return response.data;
  }
};
