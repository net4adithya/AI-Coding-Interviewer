// frontend/src/pages/intern/InterviewOverview.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { demoService } from '../../services/demoApi';
import { useAuth } from '@/contexts/AuthContext';

export function InterviewOverview() {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const [assignment, setAssignment] = useState<any>(null);
  const [assessment, setAssessment] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    demoService.getMyAssignment()
      .then(data => {
        setAssignment(data.assignment);
        setAssessment(data.assessment);
      })
      .catch(err => {
        setError(err.message || 'Failed to load your assessment.');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const isCompleted = assignment?.status === 'COMPLETED';

  const handleStart = async () => {
    if (isCompleted) return;
    setStarting(true);
    try {
      await demoService.startAssignment();
    } catch { /* non-critical */ }
    navigate('/intern/interview/workspace');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-sm text-secondary">
          <span className="material-symbols-outlined animate-spin">sync</span>
          Loading your assessment...
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="p-xl max-w-lg mx-auto mt-xl text-center">
        <span className="material-symbols-outlined text-[64px] text-outline block mb-md">assignment_late</span>
        <h2 className="font-section-heading text-section-heading text-on-surface mb-xs">No Assessment Assigned</h2>
        <p className="font-body-main text-body-main text-secondary mb-lg">
          {error || 'You do not have any active technical coding interviews assigned to you at this time. Please wait for your admin to assign one.'}
        </p>
        <button
          onClick={() => signOut()}
          className="border border-outline-variant rounded px-md py-sm text-secondary hover:bg-surface-container-high transition-colors font-navigation text-navigation cursor-pointer"
        >
          Sign Out
        </button>
      </div>
    );
  }

  const totalQ = assessment.total_questions || assessment.questions?.length || 0;
  const { EASY = 0, MEDIUM = 0, HARD = 0 } = assessment.difficulty_distribution || {};

  const rules = [
    'Read every question carefully before starting to code.',
    'Write complete, executable programs — your code reads input from stdin.',
    'Your code will be evaluated against test cases through Judge0.',
    'You can run your code as many times as needed before submitting.',
    'Once you submit, the assessment cannot be modified or re-taken.',
    'The timer begins when you click "Start Test".',
  ];

  return (
    <div className="w-full max-w-3xl mx-auto px-md py-xl flex flex-col gap-xl">
      {/* Assessment Card */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden">
        <div className="bg-primary-container/10 border-b border-outline-variant p-lg">
          <div className="flex items-start justify-between flex-wrap gap-md">
            <div>
              <h1 className="font-page-title text-page-title text-on-surface">{assessment.title}</h1>
              <p className="font-body-main text-body-main text-secondary mt-xs">{assessment.topic}</p>
            </div>
            {isCompleted ? (
              <span className="inline-flex items-center gap-xs px-md py-xs rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 font-navigation text-navigation">
                <span className="material-symbols-outlined text-[16px]">lock</span>
                Submitted & Locked
              </span>
            ) : (
              <span className="inline-flex items-center gap-xs px-md py-xs rounded-full bg-surface-container border border-outline-variant text-secondary font-navigation text-navigation">
                <span className="w-2 h-2 rounded-full bg-secondary-fixed-dim"></span>
                Not Started
              </span>
            )}
          </div>
        </div>
        <div className="p-lg grid grid-cols-2 sm:grid-cols-4 gap-lg">
          {[
            { icon: 'schedule', label: 'Duration', value: `${assessment.duration_minutes} min` },
            { icon: 'list_alt', label: 'Questions', value: `${totalQ}` },
            { icon: 'code', label: 'Language', value: assessment.language || 'Python' },
            { icon: 'bar_chart', label: 'Difficulty', value: `${EASY}E / ${MEDIUM}M / ${HARD}H` },
          ].map(({ icon, label, value }) => (
            <div key={label} className="flex flex-col gap-xs">
              <div className="flex items-center gap-xs text-secondary">
                <span className="material-symbols-outlined text-[18px]">{icon}</span>
                <span className="font-metadata text-metadata">{label}</span>
              </div>
              <span className="font-card-title text-card-title text-on-surface">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Rules & Instructions */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-lg flex flex-col gap-md">
        <h2 className="font-section-heading text-section-heading text-on-surface flex items-center gap-xs">
          <span className="material-symbols-outlined text-primary-container text-[22px]">info</span>
          Instructions & Rules
        </h2>
        <ul className="flex flex-col gap-sm">
          {rules.map((rule, index) => (
            <li key={index} className="flex items-start gap-xs text-secondary font-body-main text-body-main">
              <span className="material-symbols-outlined text-[18px] text-primary-container shrink-0 mt-0.5">check_circle</span>
              <span>{rule}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* COMPLETED BANNER OR START TEST ACTIONS */}
      {isCompleted ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-lg flex flex-col items-center text-center gap-sm">
          <span className="material-symbols-outlined text-emerald-600 text-[48px]">check_circle</span>
          <h3 className="font-section-heading text-section-heading text-emerald-900">Assessment Already Submitted</h3>
          <p className="font-body-main text-body-main text-emerald-800 max-w-md">
            You have already completed and submitted your responses for this assessment. Responses are locked and under evaluation.
          </p>
          <button
            onClick={() => navigate('/intern/interview/completed')}
            className="mt-sm bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm px-lg py-sm rounded-lg transition-colors cursor-pointer"
          >
            View Submission Details →
          </button>
        </div>
      ) : (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-lg flex flex-col gap-md">
          <label className="flex items-start gap-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-1 w-4 h-4 rounded text-primary-container focus:ring-primary-container cursor-pointer"
            />
            <span className="font-body-main text-body-main text-on-surface">
              I have read and understood all the instructions. I am ready to begin the technical assessment.
            </span>
          </label>

          <button
            onClick={handleStart}
            disabled={!agreed || starting}
            className="w-full h-12 bg-primary-container text-on-primary-container font-bold text-base rounded-lg transition-all disabled:opacity-40 flex items-center justify-center gap-xs cursor-pointer shadow-sm hover:brightness-105"
          >
            {starting ? (
              <span>Starting Assessment...</span>
            ) : (
              <>
                <span>Start Test</span>
                <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
