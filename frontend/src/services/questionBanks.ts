import api from './api';
import { demoService } from './demoApi';

export interface QuestionBank {
  id: number | string;
  owner_id?: number;
  title?: string;
  filename?: string;
  status?: string;
  question_count?: number;
  questions?: Question[];
  created_at: string;
  updated_at?: string;
}

export interface Question {
  id: number | string;
  question_bank_id?: number | string;
  title: string;
  problem_statement: string;
  topic: string;
  difficulty: string;
  expected_time_minutes?: number;
  programming_languages?: string[];
  constraints?: string;
  examples?: any[];
  test_cases?: any[];
}

const isDemo = import.meta.env.VITE_DEMO_MODE === 'true';

export const questionBanksService = {
  getQuestionBanks: async (): Promise<any[]> => {
    if (isDemo) {
      console.log('[DEMO PIPELINE] QUESTION_BANK -> getQuestionBanks');
      return demoService.getQuestionBanks();
    }
    const response = await api.get('/api/v1/assessments/question-banks');
    return response.data;
  },

  getQuestionBank: async (id: number | string): Promise<any> => {
    if (isDemo) {
      console.log(`[DEMO PIPELINE] QUESTION_BANK -> getQuestionBank ${id}`);
      return demoService.getQuestionBank(id);
    }
    const response = await api.get(`/api/v1/assessments/question-banks/${id}`);
    return response.data;
  },

  getQuestions: async (id: number | string): Promise<any[]> => {
    if (isDemo) {
      const bank = await demoService.getQuestionBank(id);
      return bank.questions || [];
    }
    const response = await api.get(`/api/v1/assessments/question-banks/${id}/questions`);
    return response.data;
  },

  uploadQuestionBank: async (file: File): Promise<any> => {
    if (isDemo) {
      console.log('[DEMO PIPELINE] QUESTION_BANK -> uploadQuestionBank');
      const res = await demoService.uploadQuestionBank(file);
      return res.question_bank || res;
    }
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/v1/assessments/question-banks/upload', formData);
    return response.data;
  },
};

