import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface RecentAssessment {
  id: number;
  title: string;
  questions: number;
  interns: number;
  status: string;
  created_at: string;
  deadline_at: string | null;
}

interface CandidateActivity {
  intern_name: string;
  assessment_title: string;
  action: string;
  timestamp: string;
}

interface DashboardStats {
  active_assessments: number;
  interns_count: number;
  submissions_count: number;
  pending_reviews: number;
  recent_assessments: RecentAssessment[];
  candidate_activity: CandidateActivity[];
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    active_assessments: 0,
    interns_count: 0,
    submissions_count: 0,
    pending_reviews: 0,
    recent_assessments: [],
    candidate_activity: []
  });

  useEffect(() => {
    api.get('/dashboard/authority/stats')
      .then(res => setStats(res.data))
      .catch(err => console.error("Failed to load dashboard stats", err));
  }, []);

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
  };

  const formatTimeAgo = (dateString: string) => {
    const d = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs} hr ago`;
    return `${Math.floor(diffHrs / 24)} days ago`;
  };

  return (
    <>
      <header className="bg-surface-container-lowest border-b custom-border w-full sticky top-0 z-10">
        <div className="flex justify-between items-center w-full px-xl py-md">
          <div className="flex flex-col">
            <h2 className="font-page-title text-page-title text-on-surface">Good morning, Authority</h2>
            <p className="font-body-main text-body-main text-secondary mt-1">Overview of your assessments and candidate activity.</p>
          </div>
          <div className="flex items-center gap-lg">
            <span className="font-body-main text-body-main text-secondary hidden lg:block">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
            </span>
            <div className="relative hidden sm:flex items-center">
              <span className="material-symbols-outlined absolute left-3 text-secondary text-[20px]">search</span>
              <input className="pl-10 pr-4 py-1.5 bg-[#F7F9FA] border border-outline-variant rounded-full text-sm focus:outline-none focus:border-primary-container transition-colors w-64" placeholder="Search..." type="text" />
            </div>
            <button className="relative p-1 text-secondary hover:text-primary-container transition-colors">
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full border border-white"></span>
            </button>
            <div className="w-9 h-9 rounded-full bg-surface-container flex items-center justify-center border custom-border shrink-0">
              <span className="material-symbols-outlined text-secondary">account_circle</span>
            </div>
          </div>
        </div>
      </header>

      <div className="p-xl max-w-max_content_width mx-auto w-full flex flex-col gap-lg">
        {/* Summary Area */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md">
          <div className="bg-surface-container-lowest border custom-border rounded p-md flex flex-col gap-1">
            <div className="flex justify-between items-center text-secondary">
              <span className="font-body-main text-body-main">Active Assessments</span>
            </div>
            <span className="text-3xl font-semibold text-on-surface mt-2">{stats.active_assessments}</span>
          </div>
          <div className="bg-surface-container-lowest border custom-border rounded p-md flex flex-col gap-1">
            <div className="flex justify-between items-center text-secondary">
              <span className="font-body-main text-body-main">Interns</span>
            </div>
            <span className="text-3xl font-semibold text-on-surface mt-2">{stats.interns_count}</span>
          </div>
          <div className="bg-surface-container-lowest border custom-border rounded p-md flex flex-col gap-1">
            <div className="flex justify-between items-center text-secondary">
              <span className="font-body-main text-body-main">Submissions</span>
            </div>
            <span className="text-3xl font-semibold text-on-surface mt-2">{stats.submissions_count}</span>
          </div>
          <div className="bg-surface-container-lowest border custom-border rounded p-md flex flex-col gap-1">
            <div className="flex justify-between items-center text-secondary">
              <span className="font-body-main text-body-main">Pending Reviews</span>
            </div>
            <span className="text-3xl font-semibold text-on-surface mt-2">{stats.pending_reviews}</span>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg mb-xl">
          <div className="lg:col-span-2">
            <section className="bg-surface-container-lowest border custom-border rounded flex flex-col h-full">
              <div className="p-md border-b custom-border flex justify-between items-center">
                <h3 className="font-section-heading text-section-heading text-on-surface">Recent Assessments</h3>
                <Link to="/authority/interviews" className="text-primary-container font-navigation text-sm hover:underline">View All</Link>
              </div>
              <div className="overflow-x-auto w-full">
                {stats.recent_assessments.length === 0 ? (
                  <div className="p-xl text-center text-secondary">No recent assessments available.</div>
                ) : (
                  <table className="w-full text-left border-collapse whitespace-nowrap">
                    <thead>
                      <tr className="bg-[#F7F9FA] border-b custom-border">
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Assessment</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Questions</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Interns</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Status</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Created</th>
                        <th className="py-3 px-4 font-navigation text-xs text-secondary uppercase tracking-wider font-medium">Deadline</th>
                        <th className="py-3 px-4"></th>
                      </tr>
                    </thead>
                    <tbody className="font-body-main text-sm">
                      {stats.recent_assessments.map(ass => (
                        <tr key={ass.id} className="border-b custom-border hover:bg-[#F7F9FA] transition-colors">
                          <td className="py-3 px-4 font-medium text-on-surface">{ass.title}</td>
                          <td className="py-3 px-4 text-secondary">{ass.questions}</td>
                          <td className="py-3 px-4 text-secondary">{ass.interns}</td>
                          <td className="py-3 px-4">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              ass.status === 'ACTIVE' || ass.status === 'PUBLISHED' ? 'bg-surface-container-highest text-primary-container border border-surface-variant' :
                              ass.status === 'COMPLETED' ? 'bg-blue-50 text-blue-700 border border-blue-100' :
                              'bg-gray-100 text-secondary border border-gray-200'
                            }`}>
                              {ass.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-secondary">{formatDate(ass.created_at)}</td>
                          <td className="py-3 px-4 text-secondary">{ass.deadline_at ? formatDate(ass.deadline_at) : 'N/A'}</td>
                          <td className="py-3 px-4 text-right">
                            <button className="text-secondary hover:text-primary-container transition-colors">
                              <span className="material-symbols-outlined text-[20px]">more_vert</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </div>
          <div className="lg:col-span-1">
            <section className="bg-surface-container-lowest border custom-border rounded flex flex-col h-full">
              <div className="p-md border-b custom-border">
                <h3 className="font-section-heading text-section-heading text-on-surface">Candidate Activity</h3>
              </div>
              <div className="p-md flex flex-col gap-lg">
                {stats.candidate_activity.length === 0 ? (
                  <div className="p-xl text-center text-secondary">No recent candidate activity.</div>
                ) : (
                  stats.candidate_activity.map((activity, idx) => (
                    <div key={idx} className="relative flex gap-3">
                      <div className="flex flex-col items-center shrink-0">
                        <div className="w-2 h-2 rounded-full bg-primary-container mt-1.5"></div>
                        {idx < stats.candidate_activity.length - 1 && (
                          <div className="w-0.5 flex-1 bg-outline-variant mt-1"></div>
                        )}
                      </div>
                      <div className="flex flex-col pb-2">
                        <p className="text-body-main text-on-surface">
                          <span className="font-semibold">{activity.intern_name}</span> {activity.action} {activity.assessment_title}
                        </p>
                        <span className="text-metadata text-secondary">{formatTimeAgo(activity.timestamp)}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </>
  );
}
