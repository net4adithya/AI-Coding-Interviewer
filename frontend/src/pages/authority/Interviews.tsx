import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { assessmentsService, AssessmentResponse } from '../../services/assessments';

export function Interviews() {
  const [assessments, setAssessments] = useState<AssessmentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    assessmentsService.getAssessments().then(data => {
      setAssessments(data);
    }).catch(err => {
      console.error("Failed to load assessments:", err);
    }).finally(() => {
      setIsLoading(false);
    });
  }, []);

  const handleAssign = async (assessmentId: number) => {
    const email = window.prompt("Enter Candidate email to assign to:");
    if (!email) return;
    
    try {
      await assessmentsService.assignAssessmentByEmail(assessmentId, email);
      alert(`Assessment assigned successfully to ${email}`);
    } catch (error: any) {
      console.error("Failed to assign:", error);
      const detail = error.response?.data?.detail || "Failed to assign assessment.";
      alert(detail);
    }
  };

  return (
    <div className="max-w-max_content_width mx-auto p-xl">
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface">Assessments</h1>
          <p className="font-body-main text-body-main text-secondary">Manage and review all technical coding interviews.</p>
        </div>
        <Link 
          to="/authority/interviews/new" 
          className="bg-primary-container text-on-primary px-md py-sm rounded font-navigation text-navigation hover:opacity-90 transition-opacity"
        >
          Create Assessment
        </Link>
      </div>

      <div className="flex gap-sm mb-lg">
        <div className="relative flex-1 max-w-md">
          <span className="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-secondary text-[20px]">search</span>
          <input 
            type="text" 
            placeholder="Search assessments..." 
            className="w-full pl-xl pr-md py-sm bg-surface-container-lowest border border-outline-variant rounded focus:border-primary focus:ring-1 focus:ring-primary outline-none text-body-main"
          />
        </div>
        <select className="px-md py-sm bg-surface-container-lowest border border-outline-variant rounded font-body-main text-body-main outline-none">
          <option>All Statuses</option>
          <option>Active</option>
          <option>Completed</option>
          <option>Draft</option>
        </select>
      </div>

      <div className="bg-surface-container-lowest border border-outline-variant rounded overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-surface-container-low border-b border-outline-variant">
            <tr>
              <th className="px-lg py-sm font-navigation text-navigation text-secondary font-medium">Title</th>
              <th className="px-lg py-sm font-navigation text-navigation text-secondary font-medium">Status</th>
              <th className="px-lg py-sm font-navigation text-navigation text-secondary font-medium">Created</th>
              <th className="px-lg py-sm font-navigation text-navigation text-secondary font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="font-body-main text-body-main text-on-surface">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-lg py-md text-center text-secondary">Loading...</td>
              </tr>
            ) : assessments.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-lg py-md text-center text-secondary">No assessments found.</td>
              </tr>
            ) : (
              assessments.map(assessment => (
                <tr key={assessment.id} className="border-b border-outline-variant hover:bg-surface-container-low transition-colors group">
                  <td className="px-lg py-md">
                    <Link to={`/authority/interviews/${assessment.id}/review`} className="font-medium text-primary hover:underline">
                      {assessment.title}
                    </Link>
                    <div className="font-metadata text-metadata text-secondary mt-1">
                      {assessment.topic_tags?.join(', ')} · {assessment.duration_minutes} mins
                    </div>
                  </td>
                  <td className="px-lg py-md">
                    <span className="inline-flex items-center gap-base px-2 py-1 rounded bg-surface-container-highest text-on-surface-variant text-xs font-medium">
                      <span className={`w-1.5 h-1.5 rounded-full ${assessment.status === 'PUBLISHED' ? 'bg-emerald-500' : 'bg-secondary'}`}></span> 
                      {assessment.status.charAt(0) + assessment.status.slice(1).toLowerCase()}
                    </span>
                  </td>
                  <td className="px-lg py-md text-secondary">{new Date(assessment.created_at).toLocaleDateString()}</td>
                  <td className="px-lg py-md text-right">
                    <button 
                      onClick={() => handleAssign(assessment.id)}
                      className="text-primary-container hover:text-primary transition-colors text-sm font-medium mr-4"
                    >
                      Assign
                    </button>
                    <button className="text-secondary hover:text-primary transition-colors p-1">
                      <span className="material-symbols-outlined text-[20px]">more_vert</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
