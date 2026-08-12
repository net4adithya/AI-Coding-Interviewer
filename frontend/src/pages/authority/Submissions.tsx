import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSubmissions, Submission } from '../../services/submissions';

export function Submissions() {
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const data = await getSubmissions();
      setSubmissions(data);
    } catch (error) {
      console.error('Failed to load submissions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg bg-background z-10 sticky top-0">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface font-semibold">Submissions</h1>
        </div>
        <div className="flex items-center gap-lg">
          <span className="font-metadata text-metadata text-secondary">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          </span>
          <button className="w-10 h-10 rounded-full bg-surface-variant flex items-center justify-center overflow-hidden border border-outline-variant hover:border-primary transition-colors cursor-pointer">
            <span className="material-symbols-outlined text-secondary">person</span>
          </button>
        </div>
      </header>

      <div className="flex-grow p-xl overflow-y-auto max-w-max_content_width mx-auto w-full">
        <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-md flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low/50">
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Candidate</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Assessment</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium hidden sm:table-cell">Submitted</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Status</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="font-body-main text-body-main text-on-surface">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="py-md text-center text-secondary">Loading submissions...</td>
                  </tr>
                ) : submissions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-md text-center text-secondary">No submissions yet.</td>
                  </tr>
                ) : (
                  submissions.map((sub) => (
                    <tr 
                      key={sub.id} 
                      className="border-b border-outline-variant hover:bg-surface-container-low transition-colors group"
                    >
                      <td className="py-sm px-md font-medium text-primary">
                        {sub.intern_name}
                        <span className="block text-metadata text-secondary font-normal">{sub.intern_email}</span>
                      </td>
                      <td className="py-sm px-md">
                        {sub.assessment_title}
                        <span className="block text-metadata text-secondary">{sub.language}</span>
                      </td>
                      <td className="py-sm px-md text-secondary hidden sm:table-cell">
                        {new Date(sub.submitted_at).toLocaleString()}
                      </td>
                      <td className="py-sm px-md">
                        <span className={`px-sm py-xs rounded-full text-xs font-medium ${
                          sub.review_status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 
                          'bg-amber-100 text-amber-800'
                        }`}>
                          {sub.review_status === 'COMPLETED' ? 'Reviewed' : 'Pending Review'}
                        </span>
                      </td>
                      <td className="py-sm px-md">
                        <button 
                          onClick={() => navigate(`/authority/interviews/${sub.submission_id}/review`)}
                          className="bg-transparent border border-outline-variant text-primary px-sm py-xs rounded hover:bg-surface-container-high transition-colors font-navigation text-sm"
                        >
                          {sub.review_status === 'COMPLETED' ? 'View Review' : 'Review'}
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
