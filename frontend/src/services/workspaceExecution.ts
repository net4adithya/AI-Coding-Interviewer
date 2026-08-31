/**
 * Workspace execution facade.
 *
 * Stage 2: Docker sandbox via /api/v1/sandbox/execution/run (Redis + worker).
 * Falls back to demo/Judge0 endpoints when sandbox is unavailable.
 */

import { demoService } from './demoApi';
import type {
  WorkspaceExecutionRequest,
  WorkspaceRunResult,
  WorkspaceTestCaseInput,
  WorkspaceTestResult,
} from '@/types/workspace';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const SANDBOX_ENABLED = import.meta.env.VITE_SANDBOX_EXECUTION !== 'false';

interface SandboxExecutionResponse {
  job_id?: string;
  status: string;
  stdout?: string;
  stderr?: string;
  exit_code?: number;
  execution_time_ms?: number;
  memory_kb?: number;
}

function mapSandboxToWorkspaceResult(data: SandboxExecutionResponse): WorkspaceRunResult {
  const accepted = data.status === 'ACCEPTED';
  return {
    status: data.status,
    stdout: data.stdout ?? '',
    stderr: data.stderr ?? '',
    compile_output: data.status === 'COMPILATION_ERROR' ? data.stderr : undefined,
    execution_time: data.execution_time_ms != null ? data.execution_time_ms / 1000 : null,
    passed: accepted,
    error_message: accepted ? undefined : data.stderr || data.status,
  };
}

async function runViaSandbox(request: WorkspaceExecutionRequest): Promise<WorkspaceRunResult | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sandbox/execution/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Sandbox execution failed (${res.status})`);
    }
    const data: SandboxExecutionResponse = await res.json();
    return mapSandboxToWorkspaceResult(data);
  } catch (err) {
    console.warn('[workspaceExecution] Sandbox unavailable, using fallback:', err);
    return null;
  }
}

export async function runWorkspaceCode(
  request: WorkspaceExecutionRequest,
): Promise<WorkspaceRunResult> {
  if (SANDBOX_ENABLED) {
    const sandboxResult = await runViaSandbox(request);
    if (sandboxResult) return sandboxResult;
  }
  return demoService.runCode(request.source_code, request.language, request.stdin);
}

export async function runWorkspaceTestCases(
  sourceCode: string,
  language: string,
  testCases: WorkspaceTestCaseInput[],
): Promise<{ results: WorkspaceTestResult[]; passed: number; total: number; all_passed: boolean }> {
  if (SANDBOX_ENABLED) {
    const results: WorkspaceTestResult[] = [];
    for (const tc of testCases) {
      const sandboxResult = await runViaSandbox({
        question_id: 'test',
        language,
        source_code: sourceCode,
        stdin: tc.input,
      });
      if (!sandboxResult) {
        return demoService.runTestCases(sourceCode, language, testCases);
      }
      const actual = (sandboxResult.stdout ?? '').trim();
      const expected = (tc.expected_output ?? '').trim();
      const passed = sandboxResult.status === 'ACCEPTED' && actual === expected;
      results.push({
        passed,
        status: sandboxResult.status,
        stdout: sandboxResult.stdout,
        stderr: sandboxResult.stderr,
        error_message: sandboxResult.error_message,
        input: tc.input,
        expected_output: tc.expected_output,
      });
    }
    const passed = results.filter((r) => r.passed).length;
    return { results, passed, total: results.length, all_passed: passed === results.length };
  }
  return demoService.runTestCases(sourceCode, language, testCases);
}
