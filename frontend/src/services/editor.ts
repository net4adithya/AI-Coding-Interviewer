import api from './api';

export interface EditorSessionResponse {
  draft_id: number;
  assignment_id: number;
  language: string;
  code: string;
  version: number;
  is_locked: boolean;
}

export interface DraftCreateRequest {
  assignment_id?: number;
  assessment_id?: number;
  question_id?: number;
  language: string;
  code: string;
}

export interface DraftResponse {
  id: number;
  assignment_id: number;
  language: string;
  code: string;
  version: number;
  status: string;
}

export interface SubmissionRequest {
  draft_id: number;
}

export interface SubmissionResponse {
  id: number;
  draft_id: number;
  intern_id: number;
  status: string;
  submitted_at: string;
}

export const editorService = {
  getSession: async (assignmentId: number, assessmentId?: number, questionId?: number): Promise<EditorSessionResponse> => {
    let url = `/api/v1/editor/session/${assignmentId}`;
    const params = new URLSearchParams();
    if (assessmentId) params.append('assessment_id', assessmentId.toString());
    if (questionId) params.append('question_id', questionId.toString());
    if (params.toString()) url += `?${params.toString()}`;
    const response = await api.get(url);
    return response.data;
  },

  saveDraft: async (payload: DraftCreateRequest): Promise<DraftResponse> => {
    const response = await api.post('/api/v1/editor/draft', payload);
    return response.data;
  },

  submitDraft: async (payload: SubmissionRequest): Promise<SubmissionResponse> => {
    const response = await api.post('/api/v1/editor/submit', payload);
    return response.data;
  },
};
