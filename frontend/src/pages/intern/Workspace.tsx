import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { assessmentsService, AssessmentResponse } from '../../services/assessments';
import { editorService, EditorSessionResponse } from '../../services/editor';
import { executionService, ExecutionTestCaseResultResponse } from '../../services/execution';

export function Workspace() {
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState<number>(0);
  const [session, setSession] = useState<EditorSessionResponse | null>(null);
  const [code, setCode] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [testResults, setTestResults] = useState<ExecutionTestCaseResultResponse[] | null>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    async function loadWorkspace() {
      try {
        const myAss = await assessmentsService.getMyAssessment();
        setAssessment(myAss);
        
        const qList = await assessmentsService.getAssessmentQuestions(myAss.id);
        setQuestions(qList);

        if (qList.length > 0) {
          await loadQuestion(0, myAss, qList);
        }
      } catch (err) {
        console.error("Failed to load workspace:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadWorkspace();
  }, []);

  const loadQuestion = async (idx: number, ass: AssessmentResponse | null = assessment, qList: any[] = questions) => {
    if (!ass || !qList[idx]) return;
    
    setIsLoading(true);
    setTestResults(null);
    try {
      const sess = await editorService.getSession(ass.assignment_id || 0, ass.id, qList[idx].id);
      setSession(sess);
      setCode(sess.code || (sess as any).template?.code || '');
      setCurrentQuestionIdx(idx);
    } catch (err) {
      console.error("Failed to load session:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeChange = (value: string | undefined) => {
    if (!value) return;
    setCode(value);
    
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    setIsSaving(true);
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        if (session && assessment && assessment.assignment_id) {
          await editorService.saveDraft({
            assignment_id: assessment.assignment_id,
            assessment_id: assessment.id,
            question_id: questions[currentQuestionIdx].id,
            language: session.language,
            code: value
          });
        }
      } catch (e) {
        console.error("Autosave failed", e);
      } finally {
        setIsSaving(false);
      }
    }, 1500);
  };

  const handleRunCode = async () => {
    if (!session || !assessment || !assessment.assignment_id) return;
    setIsExecuting(true);
    setTestResults(null);
    try {
      // First ensure draft is saved
      await editorService.saveDraft({
        assignment_id: assessment.assignment_id,
        assessment_id: assessment.id,
        question_id: questions[currentQuestionIdx].id,
        language: session.language,
        code: code
      });
      
      // Submit the draft to create a submission record for execution
      const submission = await editorService.submitDraft({ draft_id: session.draft_id });
      
      // Trigger execution pipeline
      await executionService.triggerExecution(submission.id);
      
      // Poll for results
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const summary = await executionService.getExecutionSummary(submission.id);
          if (summary.results && summary.results.length > 0) {
            setTestResults(summary.results);
            clearInterval(poll);
            setIsExecuting(false);
          }
        } catch (e) {
          // It might return 404 while processing
        }
        if (attempts > 15) {
          clearInterval(poll);
          setIsExecuting(false);
          alert("Execution timed out or failed to return results.");
        }
      }, 2000);
      
    } catch (e) {
      console.error("Failed to execute code:", e);
      setIsExecuting(false);
      alert("Failed to run code.");
    }
  };

  const handleSubmit = () => {
    // Navigate to completed
    navigate('/intern/interview/completed');
  };

  if (isLoading && !assessment) {
    return <div className="p-xl text-secondary">Loading Workspace...</div>;
  }

  const currentQ = questions[currentQuestionIdx];

  return (
    <div className="fixed inset-0 z-[100] bg-background flex flex-col font-body-main text-on-surface overflow-hidden">
      {/* Header / TopNav */}
      <header className="bg-surface border-b border-outline-variant w-full h-[60px] flex-shrink-0 flex items-center justify-between px-md md:px-lg z-10">
        <div className="flex items-center gap-md">
          <Link to="/intern/interview/overview" className="text-primary flex items-center">
            <img 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAsAALUGls9X_ukxQ3LUjcJMtHjDJV41JzsanPpASHDI841QSOtNrOwTGXuOhkligpBC6cDZ5XquGy-dKWQkg2iZmx3Y6pQ6rFyfQD36zsbfgy6lsGe8s9PD9CXzwetJnU95HJb6SJ9qeURvtOH01l4Q9fYP2kbZKkGChkxgo7pgei5iL_pVTKXo1LSXEIJgOtYH58vuDAXEeWQxTM1o0o9WsgZ6IcM83zfSKL2T8ae88tf7jcxscYrPSQqYoqGzZbZig" 
              alt="Thozhil Logo" 
              className="w-[120px] h-auto" 
            />
          </Link>
          <div className="w-[1px] h-lg bg-outline-variant hidden md:block"></div>
          <span className="font-card-title text-card-title hidden md:block">{assessment?.title || "Technical Interview"}</span>
        </div>
        <div className="flex items-center gap-xl">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-secondary text-[20px]">dns</span>
            <span className="font-navigation text-navigation text-secondary">Question {currentQuestionIdx + 1} of {questions.length}</span>
          </div>
          <div className="flex items-center gap-sm bg-surface-container py-xs px-sm rounded">
            <span className="material-symbols-outlined text-error text-[20px]">timer</span>
            <span className="font-code-snippet text-code-snippet text-error font-bold">42:18</span>
          </div>
          <div className="flex items-center gap-xs hidden md:flex min-w-[80px]">
            {isSaving ? (
              <>
                <span className="material-symbols-outlined text-secondary text-[18px] animate-spin">sync</span>
                <span className="font-metadata text-metadata text-secondary">Saving...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-primary-container text-[18px]">cloud_done</span>
                <span className="font-metadata text-metadata text-secondary">Saved</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: Problem Description */}
        <section className="w-[38%] h-full flex flex-col border-r border-outline-variant bg-surface-container-lowest overflow-y-auto">
          {currentQ ? (
            <div className="p-lg flex flex-col gap-lg">
              {/* Problem Header */}
              <div className="flex flex-col gap-sm border-b border-outline-variant pb-md">
                <h1 className="font-page-title text-page-title">{String(currentQuestionIdx + 1).padStart(2, '0')} {currentQ.title}</h1>
                <div className="flex items-center gap-sm">
                  <span className="bg-surface-container text-primary-container px-sm py-[2px] rounded text-metadata font-medium border border-primary-fixed-dim">{currentQ.difficulty || "Medium"}</span>
                  <span className="bg-surface-variant text-on-surface-variant px-sm py-[2px] rounded text-metadata">{currentQ.topic || "General"}</span>
                </div>
              </div>

              {/* Problem Description */}
              <div className="flex flex-col gap-sm">
                <h2 className="font-section-heading text-section-heading">Problem Description</h2>
                <p className="font-body-main text-body-main text-on-surface-variant whitespace-pre-wrap">
                  {currentQ.problem_statement}
                </p>
              </div>

              {/* Examples */}
              {currentQ.examples && currentQ.examples.length > 0 && (
                <div className="flex flex-col gap-sm">
                  <h2 className="font-section-heading text-section-heading">Examples</h2>
                  {currentQ.examples.map((ex: any, i: number) => (
                    <div key={i} className="bg-surface-container-low border border-outline-variant rounded-lg p-md flex flex-col gap-xs mt-sm">
                      <span className="font-card-title text-card-title">Example {i + 1}:</span>
                      <div className="font-code-snippet text-code-snippet bg-surface-container p-sm rounded text-on-surface whitespace-pre-wrap">
                        <strong>Input:</strong> {ex.input}<br />
                        <strong>Output:</strong> {ex.output}
                        {ex.explanation && <><br /><strong>Explanation:</strong> {ex.explanation}</>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Constraints */}
              {currentQ.constraints && (
                <div className="flex flex-col gap-sm mb-xl">
                  <h2 className="font-section-heading text-section-heading">Constraints</h2>
                  <div className="font-code-snippet text-code-snippet text-on-surface-variant bg-surface-container-low p-md rounded-lg border border-outline-variant whitespace-pre-wrap">
                    {currentQ.constraints}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-lg text-secondary">No question data available.</div>
          )}
        </section>

        {/* Right Panel: Editor & Output */}
        <section className="w-[62%] h-full flex flex-col bg-[#1e1e1e]">
          {/* Editor Header */}
          <div className="h-[48px] bg-[#252526] border-b border-[#3c3c3c] flex items-center justify-between px-md flex-shrink-0">
            <div className="flex items-center gap-sm">
              <span className="material-symbols-outlined text-[#569cd6] text-[18px]">code</span>
              <span className="font-navigation text-navigation text-[#cccccc]">solution.{session?.language === 'python' ? 'py' : 'txt'}</span>
            </div>
            <div className="flex items-center">
              <select 
                className="bg-[#3c3c3c] text-[#cccccc] border-none font-code-snippet text-code-snippet py-xs px-sm rounded cursor-pointer focus:ring-1 focus:ring-primary-container outline-none appearance-none"
                value={session?.language || 'python'}
                disabled
              >
                <option value="python">Python 3</option>
              </select>
            </div>
          </div>

          {/* Code Editor Area */}
          <div className="flex-1 overflow-hidden relative">
            <Editor
              height="100%"
              language={session?.language || "python"}
              theme="vs-dark"
              value={code}
              onChange={handleCodeChange}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                fontFamily: "'JetBrains Mono', monospace",
                lineHeight: 24,
                padding: { top: 16 },
                scrollBeyondLastLine: false,
                readOnly: session?.is_locked || false
              }}
            />
          </div>

          {/* Editor Footer / Actions */}
          <div className="h-[60px] bg-[#252526] border-t border-[#3c3c3c] flex items-center justify-between px-md flex-shrink-0">
            <button className="bg-[#3c3c3c] hover:bg-[#4f4f4f] text-[#cccccc] border border-[#555555] font-navigation text-navigation py-[6px] px-md rounded transition-colors flex items-center gap-xs">
              <span className="material-symbols-outlined text-[18px]">terminal</span>
              Console
            </button>
            <div className="flex gap-sm">
              <button 
                onClick={handleRunCode}
                disabled={isExecuting || session?.is_locked}
                className="bg-transparent hover:bg-[#3c3c3c] text-[#cccccc] border border-[#555555] font-navigation text-navigation py-[6px] px-md rounded transition-colors disabled:opacity-50"
              >
                {isExecuting ? 'Running...' : 'Run Code'}
              </button>
              <button 
                onClick={handleSubmit} 
                className="bg-primary-container hover:bg-primary text-on-primary font-navigation text-navigation py-[6px] px-md rounded transition-colors inline-block text-center cursor-pointer"
              >
                Submit Interview
              </button>
            </div>
          </div>

          {/* Output Panel */}
          {testResults && (
            <div className="bg-[#1e1e1e] border-t border-[#3c3c3c] h-[150px] flex flex-col flex-shrink-0">
              <div className="px-md py-xs border-b border-[#3c3c3c] flex items-center justify-between bg-[#252526]">
                <span className="font-navigation text-navigation text-[#cccccc] flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[16px]">checklist</span> Test Results
                </span>
                <span className={`font-code-snippet text-metadata ${testResults.every(r => r.is_passed) ? 'text-[#89d185]' : 'text-[#f48771]'}`}>
                  {testResults.filter(r => r.is_passed).length}/{testResults.length} Passed
                </span>
              </div>
              <div className="p-sm overflow-auto flex flex-col gap-xs">
                {testResults.map((r, i) => (
                  <div key={r.id} className="flex items-center gap-sm text-[#cccccc] font-code-snippet text-metadata">
                    {r.is_passed ? (
                      <span className="material-symbols-outlined text-[#89d185] text-[16px]">check_circle</span>
                    ) : (
                      <span className="material-symbols-outlined text-[#f48771] text-[16px]">cancel</span>
                    )}
                    Test Case {i + 1}
                    {!r.is_passed && <span className="text-[#f48771]">- Failed</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Bottom Question Navigator */}
      <footer className="h-[50px] bg-surface-container border-t border-outline-variant flex items-center justify-center px-lg flex-shrink-0">
        <div className="flex items-center gap-md">
          {questions.map((q, idx) => (
            <div key={q.id} className="flex items-center gap-md">
              {idx > 0 && <div className="w-md h-[1px] bg-outline-variant"></div>}
              <button 
                onClick={() => loadQuestion(idx)}
                className={`w-[32px] h-[32px] rounded-full flex items-center justify-center font-navigation text-navigation transition-colors ${
                  idx === currentQuestionIdx 
                    ? 'bg-primary-container text-on-primary ring-2 ring-primary-container ring-offset-2 ring-offset-surface-container shadow-sm'
                    : 'bg-surface-container-lowest text-secondary border border-outline-variant hover:bg-surface-variant'
                }`}
              >
                {String(idx + 1).padStart(2, '0')}
              </button>
            </div>
          ))}
        </div>
      </footer>
    </div>
  );
}
