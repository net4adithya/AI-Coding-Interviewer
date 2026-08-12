import api from './api';

export interface ExecutionStartResponse {
  submission_id: number;
  status: string;
  message: string;
}

export interface ExecutionTestCaseResultResponse {
  id: number;
  submission_id: number;
  test_case_id: number;
  status: string;
  is_passed: boolean;
  runtime_ms?: number;
  memory_kb?: number;
  error_message?: string;
  actual_output?: string;
}

export interface ExecutionSummaryResponse {
  submission_id: number;
  total_tests: number;
  passed_tests: number;
  pass_percentage: number;
  avg_runtime_ms: number;
  max_memory_kb: number;
  results: ExecutionTestCaseResultResponse[];
}

export const executionService = {
  triggerExecution: async (submissionId: number): Promise<ExecutionStartResponse> => {
    const response = await api.post(`/api/v1/execution/submission/${submissionId}`);
    return response.data;
  },

  getExecutionSummary: async (submissionId: number): Promise<ExecutionSummaryResponse> => {
    const response = await api.get(`/api/v1/execution/submission/${submissionId}`);
    return response.data;
  },

  listResults: async (submissionId: number): Promise<ExecutionTestCaseResultResponse[]> => {
    const response = await api.get(`/api/v1/execution/submission/${submissionId}/results`);
    return response.data;
  },
};
