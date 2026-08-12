export interface User {
  id: string;
  email: string;
  role: 'AUTHORITY' | 'INTERN';
  name?: string;
  createdAt: string;
}

export interface QuestionBank {
  id: string;
  name: string;
  description?: string;
  authorId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Question {
  id: string;
  bankId: string;
  title: string;
  description: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  topic: string;
  timeLimitMinutes: number;
  createdAt: string;
  updatedAt: string;
}

export interface Assessment {
  id: string;
  title: string;
  description?: string;
  status: 'DRAFT' | 'PUBLISHED' | 'COMPLETED';
  authorityId: string;
  createdAt: string;
  updatedAt: string;
}

export interface AssessmentQuestion {
  id: string;
  assessmentId: string;
  questionId: string;
  order: number;
}

export interface AssessmentIntern {
  id: string;
  assessmentId: string;
  internId: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REVIEWED';
  startedAt?: string;
  completedAt?: string;
}

export interface Draft {
  id: string;
  assessmentInternId: string;
  questionId: string;
  currentCode: string;
  language: string;
  lastSavedAt: string;
}

export interface DraftVersion {
  id: string;
  draftId: string;
  code: string;
  timestamp: string;
}

export interface Submission {
  id: string;
  assessmentInternId: string;
  questionId: string;
  code: string;
  language: string;
  submittedAt: string;
}

export interface ExecutionResult {
  id: string;
  submissionId?: string;
  draftId?: string;
  output?: string;
  error?: string;
  executionTimeMs: number;
  memoryUsedBytes: number;
  status: 'SUCCESS' | 'ERROR' | 'TIMEOUT';
  timestamp: string;
}

export interface ExecutionSummary {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageTimeMs: number;
}

export interface AIReview {
  id: string;
  assessmentInternId: string;
  codeQualityScore: number;
  correctnessScore: number;
  complexityScore: number;
  observations: string;
  potentialImprovements: string;
  createdAt: string;
}

export interface StaticAnalysis {
  id: string;
  submissionId: string;
  cyclomaticComplexity: number;
  lintErrors: number;
  securityIssues: number;
  details: any;
}
