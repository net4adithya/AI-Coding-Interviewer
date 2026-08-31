/** Workspace execution and submission contracts (frontend). */

export interface WorkspaceExecutionRequest {
  question_id: string;
  language: string;
  source_code: string;
  stdin: string;
}

export interface WorkspaceTestCaseInput {
  input: string;
  expected_output: string;
}

export interface WorkspaceRunResult {
  status: string;
  stdout?: string;
  stderr?: string;
  compile_output?: string;
  execution_time?: number | null;
  passed?: boolean;
  error_message?: string;
}

export interface WorkspaceTestResult {
  passed: boolean;
  status?: string;
  stdout?: string;
  stderr?: string;
  error_message?: string;
  input?: string;
  expected_output?: string;
}

export interface WorkspaceQuestionSubmission {
  language: string;
  code: string;
}

export interface WorkspaceSubmissionPayload {
  assessment_id: string;
  code_by_question: Record<string, WorkspaceQuestionSubmission>;
  final_language: string;
}
