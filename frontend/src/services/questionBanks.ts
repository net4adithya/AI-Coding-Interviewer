import api from './api';

export interface QuestionBank {
  id: number;
  owner_id: number;
  filename: string;
  status: string;
  question_count: number;
  created_at: string;
  updated_at: string;
}

export interface Question {
  id: number;
  question_bank_id: number;
  title: string;
  problem_statement: string;
  topic: string;
  difficulty: string;
  expected_time_minutes?: number;
  programming_languages: string[];
}

export const questionBanksService = {
  getQuestionBanks: async (): Promise<QuestionBank[]> => {
    const response = await api.get('/api/v1/assessments/question-banks');
    return response.data;
  },

  getQuestionBank: async (id: number): Promise<QuestionBank> => {
    const response = await api.get(`/api/v1/assessments/question-banks/${id}`);
    return response.data;
  },

  getQuestions: async (id: number): Promise<Question[]> => {
    const response = await api.get(`/api/v1/assessments/question-banks/${id}/questions`);
    return response.data;
  },

  uploadQuestionBank: async (file: File): Promise<QuestionBank> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/v1/assessments/question-banks/upload', formData);
    return response.data;
  },
};
