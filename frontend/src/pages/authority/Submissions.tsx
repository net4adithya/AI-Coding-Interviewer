// frontend/src/pages/authority/Submissions.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { demoService } from '../../services/demoApi';

export function Submissions() {
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const data = await demoService.getSubmissions();
      setSubmissions(data);
    } catch (error: any) {
      console.error('Failed to load submissions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null || score === undefined) return 'text-secondary';
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-rose-600';
  };

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg bg-background z-10 sticky top-0">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface font-semibold">Submissions</h1>
          <p className="font-body-main text-body-main text-secondary mt-xs">AI-reviewed candidate submissions</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-xs border border-outline-variant rounded px-sm py-xs text-secondary hover:bg-surface-container-high transition-colors text-sm"
        >
          <span className="material-symbols-outlined text-[16px]">refresh</span>
          Refresh
        </button>
      </header>

      <div className="flex-grow p-xl overflow-y-auto max-w-max_content_width mx-auto w-full">
        <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low/50">
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Candidate</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Assessment</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium hidden sm:table-cell">Submitted</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Score</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">AI Review</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="font-body-main text-body-main text-on-surface">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="py-xl text-center text-secondary">Loading submissions...</td>
                  </tr>
                ) : submissions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-xl text-center">
                      <span className="material-symbols-outlined text-[48px] text-outline block mb-sm">inbox</span>
                      <p className="text-secondary">No submissions yet.</p>
                      <p className="text-sm text-secondary mt-xs">Candidates appear here only after they submit their assessment.</p>
                    </td>
                  </tr>
                ) : (
                  submissions.map((sub: any) => (
                    <tr
                      key={sub.id}
                      className="border-b border-outline-variant hover:bg-surface-container-low transition-colors group"
                    >
                      <td className="py-sm px-md">
                        <div className="flex items-center gap-sm">
                          <div className="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center text-primary-container font-medium text-sm shrink-0">
                            {(sub.intern_name || 'I')[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-primary">{sub.intern_name}</p>
                            <p className="text-xs text-secondary">{sub.intern_email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-sm px-md">
                        <p className="text-on-surface">{sub.assessment_title}</p>
                        <p className="text-xs text-secondary uppercase">{sub.language}</p>
                      </td>
                      <td className="py-sm px-md text-secondary text-sm hidden sm:table-cell">
                        {new Date(sub.submitted_at).toLocaleString()}
                      </td>
                      <td className="py-sm px-md">
                        {sub.overall_score !== null && sub.overall_score !== undefined ? (
                          <span className={`font-semibold text-lg ${getScoreColor(sub.overall_score)}`}>
                            {sub.overall_score}<span className="text-secondary text-sm font-normal">/100</span>
                          </span>
                        ) : (
                          <span className="text-secondary text-sm italic">Pending</span>
                        )}
                      </td>
                      <td className="py-sm px-md">
                        <span className={`px-sm py-xs rounded-full text-xs font-medium ${
                          sub.gemini_review_status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' :
                          'bg-amber-100 text-amber-800'
                        }`}>
                          {sub.gemini_review_status === 'COMPLETED' ? 'AI Reviewed' : 'Pending Review'}
                        </span>
                      </td>
                      <td className="py-sm px-md">
                        <button
                          onClick={() => navigate(`/authority/interviews/${sub.id}/review`)}
                          className="bg-transparent border border-outline-variant text-primary px-sm py-xs rounded hover:bg-surface-container-high transition-colors font-navigation text-sm flex items-center gap-xs"
                        >
                          <span className="material-symbols-outlined text-[16px]">visibility</span>
                          View Review
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
