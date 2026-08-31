// frontend/src/pages/intern/Workspace.tsx
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { demoService } from '../../services/demoApi';
import { runWorkspaceCode, runWorkspaceTestCases } from '../../services/workspaceExecution';
import {
  DEFAULT_WORKSPACE_LANGUAGE,
  WORKSPACE_LANGUAGES,
  getStarterCode,
  getWorkspaceLanguage,
  resolveAssessmentLanguage,
} from '@/constants/workspaceLanguages';
import type { WorkspaceExecutionRequest } from '@/types/workspace';

/** questionId -> languageId -> source code */
type CodeByQuestion = Record<string, Record<string, string>>;
/** questionId -> active language */
type LanguageByQuestion = Record<string, string>;
/** questionId -> custom stdin */
type StdinByQuestion = Record<string, string>;

function DiffBadge({ diff }: { diff: string }) {
  const cls =
    diff === 'Easy'
      ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
      : diff === 'Medium'
        ? 'bg-amber-100 text-amber-700 border-amber-200'
        : 'bg-rose-100 text-rose-700 border-rose-200';
  return <span className={`px-sm py-[2px] rounded border text-xs font-medium ${cls}`}>{diff}</span>;
}

function useTimer(durationMinutes: number) {
  const [timeLeft, setTimeLeft] = useState(durationMinutes * 60);

  useEffect(() => {
    if (durationMinutes > 0) {
      setTimeLeft(durationMinutes * 60);
    }
  }, [durationMinutes]);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((t) => Math.max(0, t - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  return {
    display: `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`,
    isWarning: timeLeft < 300,
    timeRemaining: timeLeft,
  };
}

export function Workspace() {
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [codeByQuestion, setCodeByQuestion] = useState<CodeByQuestion>({});
  const [languageByQuestion, setLanguageByQuestion] = useState<LanguageByQuestion>({});
  const [stdinByQuestion, setStdinByQuestion] = useState<StdinByQuestion>({});

  const [runResult, setRunResult] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState('');
  const [testResults, setTestResults] = useState<any[] | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<'input' | 'output' | 'tests'>('input');

  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const durationMinutes = assessment?.duration_minutes || 60;
  const timer = useTimer(durationMinutes);

  const currentQ = questions[currentIdx];
  const currentQId = currentQ?.id as string | undefined;
  const selectedLanguage = currentQId
    ? languageByQuestion[currentQId] ?? DEFAULT_WORKSPACE_LANGUAGE
    : DEFAULT_WORKSPACE_LANGUAGE;
  const customInput = currentQId ? stdinByQuestion[currentQId] ?? '' : '';

  const currentCode = useMemo(() => {
    if (!currentQId) return getStarterCode(selectedLanguage);
    return codeByQuestion[currentQId]?.[selectedLanguage] ?? getStarterCode(selectedLanguage);
  }, [codeByQuestion, currentQId, selectedLanguage]);

  const ensureQuestionState = useCallback((qId: string, lang: string) => {
    setCodeByQuestion((prev) => {
      if (prev[qId]?.[lang] !== undefined) return prev;
      return { ...prev, [qId]: { ...prev[qId], [lang]: getStarterCode(lang) } };
    });
    setLanguageByQuestion((prev) => (prev[qId] ? prev : { ...prev, [qId]: lang }));
  }, []);

  useEffect(() => {
    demoService
      .getMyAssignment()
      .then((data) => {
        if (data.assignment?.status === 'COMPLETED') {
          navigate('/intern/interview/completed');
          return;
        }
        const ass = data.assessment;
        setAssessment(ass);
        const qList = ass.questions || [];
        setQuestions(qList);

        const defaultLang = resolveAssessmentLanguage(ass.language);
        qList.forEach((q: { id: string }) => ensureQuestionState(q.id, defaultLang));
        if (qList.length > 0) {
          setLanguageByQuestion({ [qList[0].id]: defaultLang });
        }
      })
      .catch((err) => setLoadError(err.message))
      .finally(() => setIsLoading(false));
  }, [navigate, ensureQuestionState]);

  const handleLanguageChange = (newLang: string) => {
    if (!currentQId) return;
    ensureQuestionState(currentQId, newLang);
    setLanguageByQuestion((prev) => ({ ...prev, [currentQId]: newLang }));
  };

  const handleCodeChange = (value: string | undefined) => {
    if (value === undefined || !currentQId) return;
    setCodeByQuestion((prev) => ({
      ...prev,
      [currentQId]: { ...prev[currentQId], [selectedLanguage]: value },
    }));
  };

  const handleStdinChange = (value: string) => {
    if (!currentQId) return;
    setStdinByQuestion((prev) => ({ ...prev, [currentQId]: value }));
  };

  const handleSelectQuestion = (idx: number) => {
    const q = questions[idx];
    if (!q) return;
    setCurrentIdx(idx);
    setRunResult(null);
    setTestResults(null);
    setRunError('');
    const lang = languageByQuestion[q.id] ?? selectedLanguage;
    ensureQuestionState(q.id, lang);
  };

  const buildExecutionRequest = (): WorkspaceExecutionRequest | null => {
    if (!currentQId || !currentCode.trim()) return null;
    return {
      question_id: currentQId,
      language: selectedLanguage,
      source_code: currentCode,
      stdin: customInput,
    };
  };

  const handleRun = async () => {
    const request = buildExecutionRequest();
    if (!request) {
      setRunError('Please write some code first.');
      return;
    }
    setIsRunning(true);
    setRunResult(null);
    setRunError('');
    setActiveTab('output');
    try {
      const result = await runWorkspaceCode(request);
      setRunResult(result);
    } catch (err: any) {
      setRunError(err.message || 'Code execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunTests = async () => {
    if (!currentCode.trim()) return;
    const testCasesToRun = currentQ?.test_cases?.filter((tc: any) => !tc.is_hidden) || [];
    const sampleTests =
      testCasesToRun.length > 0
        ? testCasesToRun
        : (currentQ?.examples || []).map((ex: any) => ({
            input: ex.input || '',
            expected_output: ex.output || '',
          }));

    if (!sampleTests.length) {
      alert('No sample test cases available for this question.');
      return;
    }

    setIsTestRunning(true);
    setTestResults(null);
    setActiveTab('tests');
    try {
      const result = await runWorkspaceTestCases(
        currentCode,
        selectedLanguage,
        sampleTests.map((tc: any) => ({
          input: tc.input || '',
          expected_output: tc.expected_output || tc.output || '',
        })),
      );
      setTestResults(result.results);
    } catch (err: any) {
      setRunError(err.message || 'Test execution failed.');
    } finally {
      setIsTestRunning(false);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const finalCodeByQ: Record<string, { language: string; code: string }> = {};
      for (const q of questions) {
        const lang = languageByQuestion[q.id] ?? selectedLanguage;
        const code = codeByQuestion[q.id]?.[lang] ?? getStarterCode(lang);
        finalCodeByQ[q.id] = { language: lang, code };
      }
      if (currentQId) {
        finalCodeByQ[currentQId] = { language: selectedLanguage, code: currentCode };
      }
      await demoService.submitAssessment({
        assessment_id: assessment.id,
        code_by_question: finalCodeByQ,
        final_language: selectedLanguage,
      });
      navigate('/intern/interview/completed');
    } catch (err: any) {
      alert(`Submission failed: ${err.message}`);
      setIsSubmitting(false);
    }
    setShowSubmitConfirm(false);
  };

  const monacoLang = getWorkspaceLanguage(selectedLanguage)?.monacoLang ?? 'python';
  const fileExt = getWorkspaceLanguage(selectedLanguage)?.fileExtension ?? 'py';
  const passedTests = testResults ? testResults.filter((r) => r.passed).length : 0;

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-[#1a1a2e] flex items-center justify-center">
        <div className="flex items-center gap-sm text-[#a0aec0]">
          <span className="material-symbols-outlined animate-spin">sync</span>
          Loading workspace...
        </div>
      </div>
    );
  }

  if (loadError || !assessment) {
    return (
      <div className="fixed inset-0 bg-[#1a1a2e] flex flex-col items-center justify-center p-xl text-center">
        <span className="material-symbols-outlined text-[64px] text-rose-400 mb-md">error</span>
        <h2 className="text-xl font-bold text-white mb-xs">Unable to Load Workspace</h2>
        <p className="text-[#a0aec0] mb-lg max-w-md">{loadError || 'Assessment data is missing.'}</p>
        <button
          onClick={() => navigate('/intern/interview/overview')}
          className="bg-[#e94560] text-white px-md py-sm rounded cursor-pointer"
        >
          Return to Overview
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[100] bg-[#1a1a2e] flex flex-col font-body-main overflow-hidden text-slate-100">
      <header className="h-[52px] bg-[#16213e] border-b border-[#0f3460] flex items-center justify-between px-md flex-shrink-0 z-10">
        <div className="flex items-center gap-md min-w-0">
          <span className="font-semibold text-white flex items-center gap-xs truncate">
            <span className="material-symbols-outlined text-[#e94560] text-[20px]">terminal</span>
            {assessment.title}
          </span>
          <span className="text-[#888] text-xs hidden sm:inline">|</span>
          <span className="text-[#a0aec0] text-xs font-mono hidden sm:inline">{questions.length} Questions</span>
        </div>

        <div className="flex items-center gap-xs bg-[#0f3460] p-[3px] rounded-lg overflow-x-auto max-w-[40vw]">
          {questions.map((q, idx) => (
            <button
              key={q.id || idx}
              onClick={() => handleSelectQuestion(idx)}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                currentIdx === idx ? 'bg-[#e94560] text-white' : 'text-[#a0aec0] hover:text-white'
              }`}
            >
              Q{idx + 1}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-md flex-shrink-0">
          <div
            className={`flex items-center gap-xs font-mono font-bold text-sm px-sm py-[4px] rounded ${
              timer.isWarning
                ? 'bg-rose-900/50 text-rose-300 border border-rose-500/30 animate-pulse'
                : 'bg-[#0f3460] text-[#e94560]'
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">schedule</span>
            <span>{timer.display}</span>
          </div>
          <button
            onClick={() => setShowSubmitConfirm(true)}
            className="bg-[#e94560] hover:bg-[#d03b53] text-white text-xs font-bold px-md py-[6px] rounded flex items-center gap-xs cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">send</span>
            Submit
          </button>
        </div>
      </header>

      <main className="flex-1 flex min-h-0 overflow-hidden">
        <aside className="w-[38%] min-w-[280px] max-w-[480px] flex flex-col border-r border-[#0f3460] bg-[#16213e] overflow-y-auto">
          {currentQ ? (
            <div className="p-lg flex flex-col gap-md text-xs">
              <div className="flex items-center justify-between gap-sm border-b border-[#0f3460] pb-sm">
                <h2 className="font-bold text-base text-white">
                  Q{currentIdx + 1}. {currentQ.title}
                </h2>
                <DiffBadge diff={currentQ.difficulty} />
              </div>

              <div>
                <span className="text-[#888] font-bold uppercase tracking-wider block mb-xs text-[10px]">
                  Problem Statement
                </span>
                <p className="text-[#cbd5e0] leading-relaxed whitespace-pre-wrap">{currentQ.problem_statement}</p>
              </div>

              {currentQ.constraints && (
                <div>
                  <span className="text-[#888] font-bold uppercase tracking-wider block mb-xs text-[10px]">Constraints</span>
                  <pre className="bg-[#0f3460]/50 text-[#a0aec0] p-sm rounded border border-[#0f3460] font-mono whitespace-pre-wrap">
                    {currentQ.constraints}
                  </pre>
                </div>
              )}

              {currentQ.input_format && (
                <div>
                  <span className="text-[#888] font-bold uppercase tracking-wider block mb-xs text-[10px]">Input Format</span>
                  <p className="text-[#cbd5e0] leading-relaxed">{currentQ.input_format}</p>
                </div>
              )}

              {currentQ.output_format && (
                <div>
                  <span className="text-[#888] font-bold uppercase tracking-wider block mb-xs text-[10px]">Output Format</span>
                  <p className="text-[#cbd5e0] leading-relaxed">{currentQ.output_format}</p>
                </div>
              )}

              {currentQ.examples?.length > 0 && (
                <div className="flex flex-col gap-sm">
                  <span className="text-[#888] font-bold uppercase tracking-wider text-[10px]">Examples</span>
                  {currentQ.examples.map((ex: any, idx: number) => (
                    <div key={idx} className="bg-[#0f3460]/40 p-sm rounded border border-[#0f3460] font-mono text-[11px]">
                      <div>
                        <span className="text-[#888]">Input:</span> <span className="text-white">{ex.input}</span>
                      </div>
                      <div>
                        <span className="text-[#888]">Output:</span>{' '}
                        <span className="text-emerald-400">{ex.output}</span>
                      </div>
                      {ex.explanation && <div className="mt-xs text-[#a0aec0] italic">{ex.explanation}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="p-md text-[#718096]">No question selected.</div>
          )}
        </aside>

        <section className="flex-1 flex flex-col min-w-0 min-h-0 bg-[#1e1e1e]">
          <div className="h-[44px] bg-[#252526] border-b border-[#3c3c3c] flex items-center justify-between px-md flex-shrink-0">
            <div className="flex items-center gap-sm">
              <span className="material-symbols-outlined text-[#569cd6] text-[16px]">code</span>
              <span className="text-[#cccccc] text-sm font-mono">solution.{fileExt}</span>
            </div>
            <select
              value={selectedLanguage}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="bg-[#3c3c3c] text-[#cccccc] border border-[#555] text-xs py-[4px] px-sm rounded cursor-pointer outline-none"
            >
              {WORKSPACE_LANGUAGES.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-h-0">
            <Editor
              key={`${currentQId}-${selectedLanguage}`}
              height="100%"
              language={monacoLang}
              theme="vs-dark"
              value={currentCode}
              onChange={handleCodeChange}
              loading={
                <div className="h-full flex items-center justify-center text-[#888] text-sm">Loading editor...</div>
              }
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
                lineHeight: 24,
                padding: { top: 16 },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                tabSize: 4,
              }}
            />
          </div>

          <div className="h-[52px] bg-[#252526] border-t border-[#3c3c3c] flex items-center justify-between px-md flex-shrink-0">
            <div className="flex items-center gap-sm">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="bg-[#0f7b0f] hover:bg-[#0d6b0d] text-white text-sm font-medium px-md py-[6px] rounded disabled:opacity-50 flex items-center gap-xs cursor-pointer"
              >
                {isRunning ? (
                  <>
                    <span className="material-symbols-outlined text-[14px] animate-spin">sync</span> Running...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[14px]">play_arrow</span> Run Code
                  </>
                )}
              </button>
              <button
                onClick={handleRunTests}
                disabled={isTestRunning}
                className="bg-transparent hover:bg-[#3c3c3c] text-[#cccccc] border border-[#555] text-sm px-md py-[6px] rounded disabled:opacity-50 flex items-center gap-xs cursor-pointer"
              >
                {isTestRunning ? (
                  <>
                    <span className="material-symbols-outlined text-[14px] animate-spin">sync</span> Testing...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[14px]">checklist</span> Run Tests
                  </>
                )}
              </button>
            </div>
            {testResults && (
              <span
                className={`text-xs font-bold ${passedTests === testResults.length ? 'text-emerald-400' : 'text-rose-400'}`}
              >
                {passedTests}/{testResults.length} tests passed
              </span>
            )}
          </div>

          <div className="h-[200px] bg-[#1e1e1e] border-t border-[#3c3c3c] flex flex-col flex-shrink-0">
            <div className="flex border-b border-[#3c3c3c] bg-[#252526]">
              {[
                { id: 'input', label: 'Custom Input', icon: 'input' },
                { id: 'output', label: 'Output', icon: 'terminal' },
                { id: 'tests', label: 'Test Results', icon: 'checklist' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'input' | 'output' | 'tests')}
                  className={`flex items-center gap-xs px-md py-xs text-xs cursor-pointer ${
                    activeTab === tab.id
                      ? 'text-[#cccccc] border-b-2 border-[#569cd6]'
                      : 'text-[#888] hover:text-[#cccccc]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="flex-1 min-h-0 overflow-auto p-sm font-mono text-xs">
              {activeTab === 'input' && (
                <textarea
                  value={customInput}
                  onChange={(e) => handleStdinChange(e.target.value)}
                  className="w-full h-full min-h-[120px] bg-transparent text-[#cccccc] font-mono text-xs resize-none outline-none placeholder:text-[#555]"
                  placeholder="Enter custom stdin input here..."
                />
              )}

              {activeTab === 'output' && (
                <div>
                  {isRunning ? (
                    <div className="flex items-center gap-xs text-[#888]">
                      <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
                      Executing...
                    </div>
                  ) : runError ? (
                    <div className="text-rose-400">{runError}</div>
                  ) : runResult ? (
                    <div className="flex flex-col gap-xs">
                      <div
                        className={`flex items-center gap-xs font-bold ${runResult.passed ? 'text-emerald-400' : 'text-amber-400'}`}
                      >
                        <span className="material-symbols-outlined text-[14px]">
                          {runResult.passed ? 'check_circle' : 'info'}
                        </span>
                        Status: {runResult.status}
                        {runResult.execution_time != null && (
                          <span className="text-[#888] font-normal">({runResult.execution_time}s)</span>
                        )}
                      </div>
                      {runResult.stdout && (
                        <div>
                          <span className="text-[#888] block">stdout:</span>
                          <pre className="text-[#e2e8f0] mt-xs whitespace-pre-wrap">{runResult.stdout}</pre>
                        </div>
                      )}
                      {runResult.stderr && (
                        <div>
                          <span className="text-rose-400 block">stderr:</span>
                          <pre className="text-rose-300 mt-xs whitespace-pre-wrap">{runResult.stderr}</pre>
                        </div>
                      )}
                      {runResult.compile_output && (
                        <div>
                          <span className="text-amber-400 block">compile output:</span>
                          <pre className="text-amber-300 mt-xs whitespace-pre-wrap">{runResult.compile_output}</pre>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-[#555]">Click &quot;Run Code&quot; to execute with custom input.</span>
                  )}
                </div>
              )}

              {activeTab === 'tests' && (
                <div>
                  {isTestRunning ? (
                    <div className="flex items-center gap-xs text-[#888]">
                      <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
                      Running test cases...
                    </div>
                  ) : testResults ? (
                    <div className="flex flex-col gap-xs">
                      <div
                        className={`text-sm font-bold ${passedTests === testResults.length ? 'text-emerald-400' : 'text-rose-400'}`}
                      >
                        {passedTests}/{testResults.length} Test Cases Passed
                      </div>
                      {testResults.map((r: any, i: number) => (
                        <div
                          key={i}
                          className={`flex items-center gap-sm p-xs rounded ${r.passed ? 'bg-emerald-900/20' : 'bg-rose-900/20'}`}
                        >
                          <span
                            className={`material-symbols-outlined text-[14px] ${r.passed ? 'text-emerald-400' : 'text-rose-400'}`}
                          >
                            {r.passed ? 'check_circle' : 'cancel'}
                          </span>
                          <span className="text-[#cccccc]">Test Case {i + 1}</span>
                          {!r.passed && r.error_message && (
                            <span className="text-rose-400 text-[11px] ml-auto">{r.error_message}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[#555]">Click &quot;Run Tests&quot; to test against problem test cases.</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>
      </main>

      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[200]">
          <div className="bg-[#16213e] border border-[#0f3460] rounded-xl p-lg max-w-md w-full mx-md flex flex-col gap-md">
            <h3 className="text-lg font-bold text-white flex items-center gap-xs">
              <span className="material-symbols-outlined text-amber-400">warning</span>
              Confirm Submission
            </h3>
            <p className="text-xs text-[#a0aec0]">
              Once submitted, your answers will be locked and cannot be changed.
            </p>
            <div className="flex items-center justify-end gap-sm pt-sm border-t border-[#0f3460]">
              <button
                onClick={() => setShowSubmitConfirm(false)}
                className="px-md py-xs text-xs font-semibold text-[#a0aec0] hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-md py-xs text-xs font-bold bg-[#e94560] hover:bg-[#d03b53] text-white rounded disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting...' : 'Yes, Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
