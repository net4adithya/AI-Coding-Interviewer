// frontend/src/pages/authority/Dashboard.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { demoService } from '../../services/demoApi';
import { useAuth } from '@/contexts/AuthContext';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

interface DashboardStats {
  active_assessments: number;
  candidates: number;
  submissions_count: number;
  pending_reviews: number;
  recent_assessments: any[];
  candidate_activity: any[];
}

export function Dashboard() {
  const { user, signOut } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    active_assessments: 0,
    candidates: 0,
    submissions_count: 0,
    pending_reviews: 0,
    recent_assessments: [],
    candidate_activity: [],
  });
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetMsg, setResetMsg] = useState('');

  useEffect(() => {
    if (DEMO_MODE) {
      demoService.getDashboardStats()
        .then(data => setStats(data))
        .catch(err => console.error('Dashboard stats failed:', err));
    }
  }, []);

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
  };

  const handleReset = async () => {
    try {
      await demoService.resetDemo();
      setResetMsg('Demo state reset successfully!');
      setShowResetConfirm(false);
      // Refresh stats
      const data = await demoService.getDashboardStats();
      setStats(data);
      setTimeout(() => setResetMsg(''), 3000);
    } catch (err: any) {
      setResetMsg(`Reset failed: ${err.message}`);
    }
  };

  return (
    <>
      <header className="bg-surface-container-lowest border-b custom-border w-full sticky top-0 z-10">
        <div className="flex justify-between items-center w-full px-xl py-md">
          <div className="flex flex-col">
            <h2 className="font-page-title text-page-title text-on-surface">
              Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {user?.name || 'Admin'}
            </h2>
            <p className="font-body-main text-body-main text-secondary mt-1">Overview of your assessments and candidate activity.</p>
          </div>
          <div className="flex items-center gap-lg">
            <span className="font-body-main text-body-main text-secondary hidden lg:block">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
            </span>
            {DEMO_MODE && (
              <button
                onClick={() => setShowResetConfirm(true)}
                className="flex items-center gap-xs text-sm border border-outline-variant rounded px-sm py-xs text-error hover:bg-error-container/20 transition-colors"
              >
                <span className="material-symbols-outlined text-[16px]">restart_alt</span>
                Reset Demo
              </button>
            )}
            <button
              onClick={() => signOut()}
              className="relative p-1 text-secondary hover:text-primary-container transition-colors"
              title="Sign out"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
            <div className="w-9 h-9 rounded-full bg-surface-container flex items-center justify-center border custom-border shrink-0">
              <span className="material-symbols-outlined text-secondary">account_circle</span>
            </div>
          </div>
        </div>
      </header>

      {/* Reset Confirmation Dialog */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-xl max-w-md w-full mx-md shadow-xl">
            <div className="flex items-center gap-sm mb-md text-error">
              <span className="material-symbols-outlined">warning</span>
              <h3 className="font-section-heading text-section-heading">Reset Demo?</h3>
            </div>
            <p className="font-body-main text-body-main text-secondary mb-lg">
              This will permanently clear all assessments, assignments, submissions, and AI reviews.
              The demo will return to its initial clean state.
            </p>
            <div className="flex gap-sm justify-end">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-md py-xs border border-outline-variant rounded font-navigation text-navigation text-on-surface hover:bg-surface-container-high transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleReset}
                className="px-md py-xs bg-error text-on-error rounded font-navigation text-navigation hover:opacity-90 transition-opacity"
              >
                Reset Demo
              </button>
            </div>
          </div>
        </div>
      )}

      {resetMsg && (
        <div className="fixed top-4 right-4 z-50 bg-surface-container-lowest border border-outline-variant rounded p-md shadow-lg text-sm text-on-surface">
          {resetMsg}
        </div>
      )}

      <div className="p-xl max-w-max_content_width mx-auto w-full flex flex-col gap-lg">
        {/* Summary Stats */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md">
          {[
            { label: 'Active Assessments', value: stats.active_assessments, icon: 'assignment' },
            { label: 'Candidates', value: stats.candidates, icon: 'group' },
            { label: 'Submissions', value: stats.submissions_count, icon: 'task_alt' },
            { label: 'Pending Reviews', value: stats.pending_reviews, icon: 'rate_review' },
          ].map(card => (
            <div key={card.label} className="bg-surface-container-lowest border custom-border rounded p-md flex flex-col gap-1">
              <div className="flex justify-between items-center text-secondary">
                <span className="font-body-main text-body-main">{card.label}</span>
                <span className="material-symbols-outlined text-[20px]">{card.icon}</span>
              </div>
              <span className="text-3xl font-semibold text-on-surface mt-2">{card.value}</span>
            </div>
          ))}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg mb-xl">
          {/* Recent Assessments */}
          <div className="lg:col-span-2">
            <section className="bg-surface-container-lowest border custom-border rounded flex flex-col h-full">
              <div className="p-md border-b custom-border flex justify-between items-center">
                <h3 className="font-section-heading text-section-heading text-on-surface">Recent Assessments</h3>
                <Link to="/authority/interviews" className="text-primary-container font-navigation text-sm hover:underline">View All</Link>
              </div>
              <div className="overflow-x-auto w-full">
                {stats.recent_assessments.length === 0 ? (
                  <div className="p-xl text-center text-secondary">
                    <span className="material-symbols-outlined text-[48px] text-outline block mb-sm">assignment</span>
                    <p className="font-body-main">No assessments yet.</p>
                    <Link to="/authority/create-assignment" className="text-primary-container text-sm hover:underline mt-xs block">Create your first assessment →</Link>
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse whitespace-nowrap">
                    <thead>
                      <tr className="bg-[#F7F9FA] border-b custom-border">
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Assessment</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Questions</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Status</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody className="font-body-main text-sm">
                      {stats.recent_assessments.map((ass: any) => (
                        <tr key={ass.id} className="border-b custom-border hover:bg-[#F7F9FA] transition-colors">
                          <td className="py-3 px-4 font-medium text-on-surface">{ass.title}</td>
                          <td className="py-3 px-4 text-secondary">{ass.questions}</td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-surface-container-highest text-primary-container border border-surface-variant">
                              {ass.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-secondary">{formatDate(ass.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </div>

          {/* Candidate Activity */}
          <div className="lg:col-span-1">
            <section className="bg-surface-container-lowest border custom-border rounded flex flex-col h-full">
              <div className="p-md border-b custom-border">
                <h3 className="font-section-heading text-section-heading text-on-surface">Candidate Activity</h3>
              </div>
              <div className="p-md flex flex-col gap-lg">
                {stats.candidate_activity.length === 0 ? (
                  <div className="p-xl text-center text-secondary">No recent candidate activity.</div>
                ) : (
                  stats.candidate_activity.map((activity: any, idx: number) => (
                    <div key={idx} className="relative flex gap-3">
                      <div className="flex flex-col items-center shrink-0">
                        <div className="w-2 h-2 rounded-full bg-primary-container mt-1.5"></div>
                        {idx < stats.candidate_activity.length - 1 && (
                          <div className="w-0.5 flex-1 bg-outline-variant mt-1"></div>
                        )}
                      </div>
                      <div className="flex flex-col pb-2">
                        <p className="text-body-main text-on-surface">
                          <span className="font-semibold">{activity.intern_name}</span> {activity.action} <em>{activity.assessment_title}</em>
                        </p>
                        <span className="text-metadata text-secondary">{new Date(activity.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md">
          <Link to="/authority/create-assignment" className="bg-primary-container text-white rounded-xl p-md flex items-center gap-md hover:bg-sky-600 transition-all group shadow-sm">
            <span className="material-symbols-outlined text-[28px]" style={{ fontVariationSettings: '"FILL" 1' }}>add_circle</span>
            <div>
              <p className="font-card-title text-card-title font-semibold">+ Create Assignment</p>
              <p className="text-metadata opacity-90 text-xs">Build assessment from Question Bank</p>
            </div>
          </Link>
          <Link to="/authority/question-bank" className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex items-center gap-md hover:bg-surface-container-low transition-colors group">
            <span className="material-symbols-outlined text-[28px] text-sky-600">upload_file</span>
            <div>
              <p className="font-card-title text-card-title text-on-surface font-semibold">Question Bank</p>
              <p className="text-metadata text-secondary text-xs">Upload & manage PDF question banks</p>
            </div>
          </Link>
          <Link to="/authority/candidates" className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex items-center gap-md hover:bg-surface-container-low transition-colors group">
            <span className="material-symbols-outlined text-[28px] text-sky-600">person_add</span>
            <div>
              <p className="font-card-title text-card-title text-on-surface font-semibold">Candidates</p>
              <p className="text-metadata text-secondary text-xs">Assign assessments to interns</p>
            </div>
          </Link>
          <Link to="/authority/submissions" className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex items-center gap-md hover:bg-surface-container-low transition-colors group">
            <span className="material-symbols-outlined text-[28px] text-sky-600">rate_review</span>
            <div>
              <p className="font-card-title text-card-title text-on-surface font-semibold">Submissions</p>
              <p className="text-metadata text-secondary text-xs">Review results & Gemini code analysis</p>
            </div>
          </Link>
        </div>
      </div>
    </>
  );
}
