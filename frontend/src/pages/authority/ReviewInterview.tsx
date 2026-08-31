// frontend/src/pages/authority/ReviewInterview.tsx
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { demoService } from '../../services/demoApi';

const SCORE_CATEGORIES = [
  { key: 'correctness_score', label: 'Correctness', weight: 30, icon: 'check_circle' },
  { key: 'algorithm_score', label: 'Algorithm', weight: 15, icon: 'account_tree' },
  { key: 'time_complexity_score', label: 'Time Complexity', weight: 10, icon: 'speed' },
  { key: 'space_complexity_score', label: 'Space Complexity', weight: 5, icon: 'memory' },
  { key: 'readability_score', label: 'Readability', weight: 10, icon: 'visibility' },
  { key: 'maintainability_score', label: 'Maintainability', weight: 10, icon: 'build' },
  { key: 'security_score', label: 'Security', weight: 10, icon: 'security' },
  { key: 'performance_score', label: 'Performance', weight: 5, icon: 'bolt' },
  { key: 'documentation_score', label: 'Documentation', weight: 5, icon: 'description' },
];

function ScoreBar({ score }: { score: number }) {
  const color = score >= 80 ? 'bg-emerald-500' : score >= 60 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-sm w-full">
      <div className="flex-1 h-2 bg-surface-container-high rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-sm font-semibold min-w-[36px] text-right ${
        score >= 80 ? 'text-emerald-600' : score >= 60 ? 'text-amber-600' : 'text-rose-600'
      }`}>{score}</span>
    </div>
  );
}

export function ReviewInterview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pollingReview, setPollingReview] = useState(false);
  const [decision, setDecision] = useState<string | null>(null);
  const [savingDecision, setSavingDecision] = useState(false);
  const [decisionMsg, setDecisionMsg] = useState('');

  useEffect(() => {
    if (!id) return;
    demoService.getSubmissionDetail(id)
      .then(d => {
        setData(d);
        // Load existing decision if any
        if (d.authority_decision?.decision) {
          setDecision(d.authority_decision.decision);
        }
        // If review is pending, start polling
        if (d.submission?.gemini_review_status === 'PENDING') {
          setPollingReview(true);
        }
      })
      .catch(err => console.error('Failed to load review:', err))
      .finally(() => setIsLoading(false));
  }, [id]);

  const handleDecision = async (dec: string) => {
    if (!id) return;
    setSavingDecision(true);
    setDecisionMsg('');
    try {
      await demoService.saveDecision(id, dec);
      setDecision(dec);
      setDecisionMsg(`Decision saved: ${dec.replace('_', ' ')}`);
      setTimeout(() => setDecisionMsg(''), 4000);
    } catch (err: any) {
      setDecisionMsg(`Failed to save decision: ${err.message}`);
    } finally {
      setSavingDecision(false);
    }
  };

  // Poll for Gemini review completion
  useEffect(() => {
    if (!pollingReview || !id) return;
    const interval = setInterval(async () => {
      try {
        const status = await demoService.getReviewStatus(id);
        if (status.review_available) {
          const updated = await demoService.getSubmissionDetail(id);
          setData(updated);
          setPollingReview(false);
          clearInterval(interval);
        }
      } catch { /* keep polling */ }
    }, 3000);
    return () => clearInterval(interval);
  }, [pollingReview, id]);

  if (isLoading) {
    return <div className="p-xl text-secondary flex items-center gap-sm"><span className="material-symbols-outlined animate-spin">sync</span> Loading review...</div>;
  }
  if (!data) {
    return <div className="p-xl text-secondary">Review not found or submission not available.</div>;
  }

  const { submission, assessment, gemini_review: review } = data;
  const intern_name = submission?.intern_email?.split('@')[0]?.replace(/^\w/, (c: string) => c.toUpperCase()) || 'Intern';

  // Extract the first submitted code for display
  const codeByQuestion = submission?.code_by_question || {};
  const firstEntry = Object.values(codeByQuestion)[0] as any;
  const submittedCode = firstEntry?.code || '';
  const submittedLanguage = firstEntry?.language || submission?.final_language || 'python';

  const overallScore = review?.overall_score;
  const hasReview = review && !review.error;

  return (
    <div className="max-w-max_content_width mx-auto p-xl flex flex-col gap-xl">
      {/* Header */}
      <div className="flex justify-between items-start flex-wrap gap-md">
        <div>
          <button
            onClick={() => navigate('/authority/submissions')}
            className="flex items-center gap-xs text-secondary hover:text-primary-container transition-colors text-sm mb-sm"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Back to Submissions
          </button>
          <h1 className="font-page-title text-page-title text-on-surface">AI Interview Review</h1>
        </div>
        <div className="flex items-center gap-sm">
          {pollingReview && (
            <span className="flex items-center gap-xs text-amber-600 text-sm">
              <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
              AI review generating...
            </span>
          )}
          {hasReview && overallScore !== undefined && (
            <div className={`text-3xl font-bold ${
              overallScore >= 80 ? 'text-emerald-600' : overallScore >= 60 ? 'text-amber-600' : 'text-rose-600'
            }`}>
              {overallScore}<span className="text-secondary text-lg font-normal">/100</span>
            </div>
          )}
        </div>
      </div>

      {/* Candidate Card */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-lg flex items-center justify-between flex-wrap gap-md">
        <div className="flex items-center gap-lg">
          <div className="w-16 h-16 rounded-full bg-primary-container/20 flex items-center justify-center text-primary-container text-2xl font-bold">
            {intern_name[0]}
          </div>
          <div>
            <h2 className="font-card-title text-card-title text-on-surface">{intern_name}</h2>
            <p className="font-metadata text-metadata text-secondary mt-xs">{submission?.intern_email}</p>
            <p className="font-metadata text-metadata text-secondary">{assessment?.title}</p>
          </div>
        </div>
        <div className="flex gap-xl">
          {[
            { label: 'Submitted', value: submission?.submitted_at ? new Date(submission.submitted_at).toLocaleString() : 'N/A' },
            { label: 'Language', value: submittedLanguage?.toUpperCase() || 'N/A' },
            { label: 'Duration', value: assessment ? `${assessment.duration_minutes} min` : 'N/A' },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="font-metadata text-metadata text-secondary">{label}</p>
              <p className="font-body-main font-medium text-on-surface">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* AI Review Section */}
      {!hasReview ? (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-xl text-center">
          {pollingReview ? (
            <div className="flex flex-col items-center gap-md">
              <span className="material-symbols-outlined text-[48px] text-primary-container animate-spin">auto_awesome</span>
              <p className="font-section-heading text-section-heading text-on-surface">Gemini is reviewing the code...</p>
              <p className="text-secondary text-sm">This may take 15–30 seconds. The page will update automatically.</p>
            </div>
          ) : review?.error ? (
            <div className="text-error">
              <span className="material-symbols-outlined text-[48px] block mb-sm">error</span>
              <p className="font-section-heading">AI Review Unavailable</p>
              <p className="text-sm mt-xs">{review.error}</p>
            </div>
          ) : (
            <p className="text-secondary">No review data available.</p>
          )}
        </div>
      ) : (
        <>
          {/* Score Cards Grid */}
          <section>
            <h3 className="font-section-heading text-section-heading text-on-surface mb-md flex items-center gap-sm">
              <span className="material-symbols-outlined text-primary-container">analytics</span>
              Score Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
              {SCORE_CATEGORIES.map(cat => {
                const score = review?.[cat.key] ?? 0;
                return (
                  <div key={cat.key} className="bg-surface-container-lowest border border-outline-variant rounded p-md flex flex-col gap-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-xs">
                        <span className="material-symbols-outlined text-[18px] text-primary-container">{cat.icon}</span>
                        <span className="font-navigation text-navigation text-on-surface">{cat.label}</span>
                      </div>
                      <span className="text-xs text-secondary">{cat.weight}%</span>
                    </div>
                    <ScoreBar score={score} />
                  </div>
                );
              })}
            </div>

            {/* Overall Score */}
            <div className={`mt-md p-lg rounded-lg border flex items-center justify-between ${
              (overallScore ?? 0) >= 80 ? 'bg-emerald-50 border-emerald-200' :
              (overallScore ?? 0) >= 60 ? 'bg-amber-50 border-amber-200' :
              'bg-rose-50 border-rose-200'
            }`}>
              <div>
                <p className="font-navigation text-navigation text-secondary">Overall Score (Weighted)</p>
                <p className="text-metadata text-secondary text-sm">Correctness 30% · Algorithm 15% · Complexity 15% · Readability 10% · Maintainability 10% · Security 10% · Others 10%</p>
              </div>
              <div className={`text-5xl font-bold ${
                (overallScore ?? 0) >= 80 ? 'text-emerald-600' :
                (overallScore ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
              }`}>
                {overallScore}<span className="text-2xl font-normal text-secondary">/100</span>
              </div>
            </div>
          </section>

          {/* Complexity */}
          {(review?.time_complexity || review?.space_complexity) && (
            <div className="flex gap-md flex-wrap">
              <div className="bg-surface-container-lowest border border-outline-variant rounded p-md flex-1 min-w-[200px]">
                <p className="text-xs text-secondary uppercase tracking-wider mb-xs">Time Complexity</p>
                <p className="font-code-snippet text-card-title text-primary-container">{review.time_complexity}</p>
              </div>
              <div className="bg-surface-container-lowest border border-outline-variant rounded p-md flex-1 min-w-[200px]">
                <p className="text-xs text-secondary uppercase tracking-wider mb-xs">Space Complexity</p>
                <p className="font-code-snippet text-card-title text-primary-container">{review.space_complexity}</p>
              </div>
            </div>
          )}

          {/* AI Summary */}
          <section className="bg-surface-container-lowest border border-outline-variant rounded-lg p-lg">
            <h3 className="font-section-heading text-section-heading text-on-surface mb-md flex items-center gap-sm">
              <span className="material-symbols-outlined text-primary-container">auto_awesome</span>
              Gemini AI Summary
            </h3>
            <p className="font-body-main text-body-main text-on-surface-variant mb-lg">{review.summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
              <div>
                <h4 className="font-card-title text-card-title text-emerald-700 flex items-center gap-xs mb-sm">
                  <span className="material-symbols-outlined text-[18px]">thumb_up</span>
                  Strengths
                </h4>
                <ul className="flex flex-col gap-xs">
                  {(review.strengths || []).map((s: string, i: number) => (
                    <li key={i} className="flex items-start gap-sm text-body-main text-on-surface-variant">
                      <span className="material-symbols-outlined text-emerald-500 text-[16px] mt-[2px] shrink-0">check</span>
                      {s}
                    </li>
                  ))}
                  {!review.strengths?.length && <li className="text-secondary text-sm">No strengths highlighted.</li>}
                </ul>
              </div>

              <div>
                <h4 className="font-card-title text-card-title text-rose-700 flex items-center gap-xs mb-sm">
                  <span className="material-symbols-outlined text-[18px]">thumb_down</span>
                  Weaknesses
                </h4>
                <ul className="flex flex-col gap-xs">
                  {(review.weaknesses || []).map((w: string, i: number) => (
                    <li key={i} className="flex items-start gap-sm text-body-main text-on-surface-variant">
                      <span className="material-symbols-outlined text-rose-500 text-[16px] mt-[2px] shrink-0">close</span>
                      {w}
                    </li>
                  ))}
                  {!review.weaknesses?.length && <li className="text-secondary text-sm">No weaknesses highlighted.</li>}
                </ul>
              </div>
            </div>

            {review.suggestions?.length > 0 && (
              <div className="mt-lg border-t border-outline-variant pt-lg">
                <h4 className="font-card-title text-card-title text-on-surface flex items-center gap-xs mb-sm">
                  <span className="material-symbols-outlined text-[18px] text-primary-container">lightbulb</span>
                  Suggestions
                </h4>
                <ul className="flex flex-col gap-xs">
                  {review.suggestions.map((s: string, i: number) => (
                    <li key={i} className="flex items-start gap-sm text-body-main text-on-surface-variant">
                      <span className="text-primary-container font-bold text-sm mt-[2px] shrink-0">{i + 1}.</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-metadata text-secondary italic mt-lg">
              AI-generated analysis is provided as decision support. Final evaluation remains with the interview team.
            </p>
          </section>
        </>
      )}

      {/* Submitted Code */}
      {submittedCode && (
        <section>
          <h3 className="font-section-heading text-section-heading text-on-surface mb-md flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary-container">code</span>
            Submitted Code
          </h3>
          <div className="rounded overflow-hidden border border-outline-variant">
            <div className="bg-[#252526] px-md py-xs flex items-center gap-sm border-b border-[#3c3c3c]">
              <span className="material-symbols-outlined text-[#569cd6] text-[16px]">code</span>
              <span className="text-[#cccccc] text-sm font-code-snippet">{submittedLanguage}</span>
              <span className="ml-auto text-[#888] text-xs">Read-only</span>
            </div>
            <Editor
              height="400px"
              language={submittedLanguage === 'c++' ? 'cpp' : submittedLanguage}
              theme="vs-dark"
              value={submittedCode}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: "'JetBrains Mono', monospace",
                lineHeight: 22,
                padding: { top: 12 },
                scrollBeyondLastLine: false,
              }}
            />
          </div>
        </section>
      )}

      {/* ── AUTHORITY DECISION ─────────────────────────────────────────────── */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-xl">
        <h3 className="font-section-heading text-section-heading text-on-surface mb-sm flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary-container">gavel</span>
          Authority Decision
        </h3>
        <p className="text-secondary text-sm mb-lg">
          Record your hiring decision for this candidate based on the code quality, AI review, and overall performance.
        </p>

        {/* Decision Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-md mb-lg">
          {[
            {
              key: 'RECOMMENDED',
              label: 'Recommended',
              icon: 'thumb_up',
              active: 'bg-emerald-600 text-white shadow-md ring-2 ring-emerald-300',
              idle: 'border-2 border-emerald-300 text-emerald-700 hover:bg-emerald-50',
            },
            {
              key: 'NEEDS_REVIEW',
              label: 'Needs Review',
              icon: 'pending',
              active: 'bg-amber-500 text-white shadow-md ring-2 ring-amber-300',
              idle: 'border-2 border-amber-300 text-amber-700 hover:bg-amber-50',
            },
            {
              key: 'NOT_RECOMMENDED',
              label: 'Not Recommended',
              icon: 'thumb_down',
              active: 'bg-rose-600 text-white shadow-md ring-2 ring-rose-300',
              idle: 'border-2 border-rose-300 text-rose-700 hover:bg-rose-50',
            },
          ].map(opt => (
            <button
              key={opt.key}
              onClick={() => handleDecision(opt.key)}
              disabled={savingDecision}
              className={`flex items-center justify-center gap-sm py-lg px-md rounded-xl font-navigation text-navigation transition-all ${
                decision === opt.key ? opt.active : opt.idle
              } disabled:opacity-60`}
            >
              <span className="material-symbols-outlined text-[22px]" style={decision === opt.key ? { fontVariationSettings: '"FILL" 1' } : {}}>
                {opt.icon}
              </span>
              {opt.label}
              {decision === opt.key && (
                <span className="material-symbols-outlined text-[16px] ml-xs">check_circle</span>
              )}
            </button>
          ))}
        </div>

        {/* Current Decision Display */}
        {decision && (
          <div className={`flex items-center gap-sm p-md rounded-lg border ${
            decision === 'RECOMMENDED' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' :
            decision === 'NEEDS_REVIEW' ? 'bg-amber-50 border-amber-200 text-amber-800' :
            'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>
              {decision === 'RECOMMENDED' ? 'check_circle' : decision === 'NEEDS_REVIEW' ? 'pending' : 'cancel'}
            </span>
            <div>
              <p className="font-semibold">
                Current Decision: {decision.replace('_', ' ')}
              </p>
              <p className="text-sm opacity-70">This decision is saved and will persist as long as the demo server is running.</p>
            </div>
          </div>
        )}

        {/* Feedback Message */}
        {decisionMsg && (
          <div className="mt-sm text-sm text-secondary bg-surface-container rounded p-sm">
            {decisionMsg}
          </div>
        )}

        {!decision && (
          <p className="text-secondary text-sm italic">
            No decision recorded yet. Select one of the options above.
          </p>
        )}
      </section>
    </div>
  );
}
