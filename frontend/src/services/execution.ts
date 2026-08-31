import api from './api';
import { demoService } from './demoApi';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export interface ExecutionStartResponse {
  submission_id: number | string;
  status: string;
  message: string;
}

export interface ExecutionTestCaseResultResponse {
  id: number | string;
  submission_id: number | string;
  test_case_id: number | string;
  status: string;
  is_passed: boolean;
  runtime_ms?: number;
  memory_kb?: number;
  error_message?: string;
  actual_output?: string;
}

export interface ExecutionSummaryResponse {
  submission_id: number | string;
  total_tests: number;
  passed_tests: number;
  pass_percentage: number;
  avg_runtime_ms: number;
  max_memory_kb: number;
  results: ExecutionTestCaseResultResponse[];
}

export const executionService = {
  triggerExecution: async (submissionId: number | string): Promise<any> => {
    if (DEMO_MODE) return { submission_id: submissionId, status: 'completed', message: 'Executed in demo mode' };
    const response = await api.post(`/api/v1/execution/submission/${submissionId}`);
    return response.data;
  },

  getExecutionSummary: async (submissionId: number | string): Promise<any> => {
    if (DEMO_MODE) return demoService.getSubmissionDetail(String(submissionId));
    const response = await api.get(`/api/v1/execution/submission/${submissionId}`);
    return response.data;
  },

  listResults: async (submissionId: number | string): Promise<any[]> => {
    if (DEMO_MODE) return [];
    const response = await api.get(`/api/v1/execution/submission/${submissionId}/results`);
    return response.data;
  },
};
