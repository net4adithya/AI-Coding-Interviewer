import { useState, useEffect } from 'react';
import { getCandidates, assignCandidateByEmail, Candidate } from '../../services/candidates';
import { assessmentsService, AssessmentResponse } from '../../services/assessments';

export function Candidates() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [assessments, setAssessments] = useState<AssessmentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Form state
  const [email, setEmail] = useState('');
  const [assessmentId, setAssessmentId] = useState<string>('');
  const [isAssigning, setIsAssigning] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [cands, assts] = await Promise.all([
        getCandidates(),
        assessmentsService.getAssessments()
      ]);
      setCandidates(cands);
      
      const published = assts.filter(a => a.status === 'PUBLISHED' || a.status === 'ASSIGNED');
      setAssessments(published);
      if (published.length > 0) {
        setAssessmentId(published[0].id.toString());
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!email || !assessmentId) {
      alert('Please enter an email and select an assessment.');
      return;
    }
    
    setIsAssigning(true);
    try {
      await assignCandidateByEmail(parseInt(assessmentId), email);
      setIsModalOpen(false);
      setEmail('');
      await fetchData();
    } catch (error: any) {
      console.error('Assignment failed:', error);
      const detail = error.response?.data?.detail || 'Assignment failed. Check if user exists and is not already assigned.';
      alert(detail);
    } finally {
      setIsAssigning(false);
    }
  };

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg bg-background z-10 sticky top-0">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface font-semibold">Candidates</h1>
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
        <div className="flex justify-between items-center mb-md">
          <h2 className="font-section-heading text-section-heading text-on-surface">Invited Candidates</h2>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="bg-primary-container text-on-primary px-md py-xs rounded hover:opacity-90 transition-opacity font-navigation text-navigation"
          >
            Assign Assessment
          </button>
        </div>

        <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-md flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low/50">
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Candidate Email</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Assessment</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Status</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium hidden sm:table-cell">Assigned Date</th>
                </tr>
              </thead>
              <tbody className="font-body-main text-body-main text-on-surface">
                {isLoading ? (
                  <tr>
                    <td colSpan={4} className="py-md text-center text-secondary">Loading candidates...</td>
                  </tr>
                ) : candidates.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-md text-center text-secondary">No candidates assigned yet.</td>
                  </tr>
                ) : (
                  candidates.map((candidate) => (
                    <tr 
                      key={candidate.id} 
                      className="border-b border-outline-variant hover:bg-surface-container-low transition-colors"
                    >
                      <td className="py-sm px-md font-medium text-primary">
                        {candidate.intern_name || candidate.intern_email}
                        {candidate.intern_name && <span className="block text-metadata text-secondary">{candidate.intern_email}</span>}
                      </td>
                      <td className="py-sm px-md">{candidate.assessment_title}</td>
                      <td className="py-sm px-md">
                        <span className={`px-sm py-xs rounded-full text-xs font-medium ${
                          candidate.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 
                          candidate.status === 'ASSIGNED' ? 'bg-blue-100 text-blue-800' :
                          'bg-surface-variant text-secondary'
                        }`}>
                          {candidate.status}
                        </span>
                      </td>
                      <td className="py-sm px-md text-secondary hidden sm:table-cell">
                        {new Date(candidate.assigned_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface-container-lowest p-xl rounded-DEFAULT shadow-lg w-full max-w-md flex flex-col gap-md">
            <h2 className="font-section-heading text-section-heading text-on-surface">Assign Assessment</h2>
            
            <div className="flex flex-col gap-xs">
              <label className="font-navigation text-navigation text-on-surface">Candidate Email</label>
              <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="intern@example.com"
                className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 outline-none bg-surface-container-lowest w-full"
              />
            </div>
            
            <div className="flex flex-col gap-xs">
              <label className="font-navigation text-navigation text-on-surface">Select Assessment</label>
              <select 
                value={assessmentId}
                onChange={e => setAssessmentId(e.target.value)}
                className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 outline-none bg-surface-container-lowest w-full"
              >
                {assessments.map(a => (
                  <option key={a.id} value={a.id}>{a.title} ({a.total_questions} qs)</option>
                ))}
              </select>
              {assessments.length === 0 && (
                <p className="text-metadata text-amber-600">No published assessments available.</p>
              )}
            </div>

            <div className="flex justify-end gap-sm mt-md">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-md py-xs rounded border border-outline-variant text-on-surface hover:bg-surface-container-high transition-colors font-navigation"
              >
                Cancel
              </button>
              <button 
                onClick={handleAssign}
                disabled={isAssigning || assessments.length === 0}
                className="bg-primary-container text-on-primary px-md py-xs rounded hover:opacity-90 transition-opacity font-navigation disabled:opacity-50"
              >
                {isAssigning ? 'Assigning...' : 'Assign'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
