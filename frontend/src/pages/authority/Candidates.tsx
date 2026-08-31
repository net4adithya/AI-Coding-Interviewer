// frontend/src/pages/authority/Candidates.tsx
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { demoService } from '../../services/demoApi';

export function Candidates() {
  const [searchParams] = useSearchParams();
  const preselectedAssessmentId = searchParams.get('assessmentId');

  const [candidates, setCandidates] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [assigningTo, setAssigningTo] = useState<string | null>(null);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(preselectedAssessmentId || '');
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    Promise.all([
      demoService.getCandidates(),
      demoService.getAssessments(),
    ]).then(([cands, assessments]) => {
      setCandidates(cands);
      setAssessments(assessments);
      if (!selectedAssessmentId && assessments.length > 0) {
        setSelectedAssessmentId(assessments[0].id);
      }
    }).catch(err => {
      setErrorMsg(`Failed to load data: ${err.message}`);
    }).finally(() => setIsLoading(false));
  }, []);

  const handleAssign = async (candidateEmail: string) => {
    if (!selectedAssessmentId) {
      setErrorMsg('Please select an assessment first.');
      return;
    }
    setAssigningTo(candidateEmail);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await demoService.assignAssessment(selectedAssessmentId, candidateEmail);
      setSuccessMsg(`✓ Assessment assigned successfully to ${candidateEmail}`);
      // Refresh candidates
      const updated = await demoService.getCandidates();
      setCandidates(updated);
    } catch (err: any) {
      setErrorMsg(`Assignment failed: ${err.message}`);
    } finally {
      setAssigningTo(null);
    }
  };

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg sticky top-0 bg-background z-10">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface font-semibold">Candidates</h1>
          <p className="font-body-main text-body-main text-secondary mt-xs">Assign assessments to candidates</p>
        </div>
      </header>

      <div className="flex-grow px-xl pb-xl max-w-max_content_width mx-auto w-full flex flex-col gap-lg">
        {successMsg && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded p-md flex items-center gap-sm">
            <span className="material-symbols-outlined text-emerald-600">check_circle</span>
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="bg-error-container/20 border border-error/30 text-error rounded p-md flex items-center gap-sm">
            <span className="material-symbols-outlined">error</span>
            {errorMsg}
          </div>
        )}

        {/* Assessment Selector */}
        <section className="bg-surface-container-lowest border border-outline-variant rounded p-md">
          <h2 className="font-card-title text-card-title text-on-surface mb-md">Select Assessment to Assign</h2>
          {assessments.length === 0 ? (
            <div className="text-secondary text-sm">
              No assessments available. <Link to="/authority/create-assignment" className="text-sky-700 font-bold hover:underline">Create one first →</Link>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-sm items-start sm:items-center">
              <select
                value={selectedAssessmentId}
                onChange={e => setSelectedAssessmentId(e.target.value)}
                className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary outline-none bg-surface-container-lowest appearance-none flex-1 max-w-md"
              >
                <option value="">-- Select assessment --</option>
                {assessments.map((a: any) => (
                  <option key={a.id} value={a.id}>
                    {a.title} ({a.total_questions} questions · {a.duration_minutes} min · {a.language})
                  </option>
                ))}
              </select>
              {selectedAssessmentId && (
                <div className="flex items-center gap-xs text-sm text-secondary">
                  <span className="material-symbols-outlined text-[16px] text-primary-container">check_circle</span>
                  Assessment selected
                </div>
              )}
            </div>
          )}
        </section>

        {/* Candidates Table */}
        <section className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT flex flex-col">
          <div className="p-md border-b border-outline-variant flex justify-between items-center">
            <h2 className="font-card-title text-card-title text-on-surface">Demo Candidates</h2>
            <span className="text-sm text-secondary">{candidates.length} candidate{candidates.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low/50">
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Candidate</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Email</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Status</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Assigned Assessment</th>
                  <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="font-body-main text-body-main text-on-surface">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="py-xl text-center text-secondary">Loading candidates...</td>
                  </tr>
                ) : candidates.map((c: any) => (
                  <tr key={c.id} className="border-b border-outline-variant hover:bg-surface-container-low transition-colors">
                    <td className="py-sm px-md">
                      <div className="flex items-center gap-sm">
                        <div className="w-9 h-9 rounded-full bg-primary-container/20 flex items-center justify-center text-primary-container font-medium text-sm">
                          {c.name[0]}
                        </div>
                        <span className="font-medium">{c.name}</span>
                      </div>
                    </td>
                    <td className="py-sm px-md text-secondary">{c.email}</td>
                    <td className="py-sm px-md">
                      <span className={`inline-flex items-center gap-xs px-sm py-xs rounded-full text-xs font-medium ${
                        c.status === 'SUBMITTED' || c.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-700' :
                        c.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700' :
                        c.status === 'ASSIGNED' ? 'bg-amber-100 text-amber-700' :
                        'bg-surface-container text-secondary'
                      }`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        {c.status || 'Available'}
                      </span>
                    </td>
                    <td className="py-sm px-md text-secondary">
                      {c.assigned_assessment || <span className="text-outline italic">Not assigned</span>}
                    </td>
                    <td className="py-sm px-md">
                      <button
                        onClick={() => handleAssign(c.email)}
                        disabled={assigningTo === c.email || !selectedAssessmentId}
                        className="bg-primary-container text-on-primary text-sm px-md py-xs rounded hover:bg-primary transition-colors disabled:opacity-50 flex items-center gap-xs"
                      >
                        {assigningTo === c.email ? (
                          <>
                            <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
                            Assigning...
                          </>
                        ) : (
                          <>
                            <span className="material-symbols-outlined text-[14px]">assignment_ind</span>
                            Assign Assessment
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Manual email assignment */}
        <section className="bg-surface-container-lowest border border-outline-variant rounded p-md">
          <h2 className="font-card-title text-card-title text-on-surface mb-sm">Assign by Email</h2>
          <p className="text-sm text-secondary mb-md">Enter any intern's email address to assign the selected assessment.</p>
          <ManualAssign
            selectedAssessmentId={selectedAssessmentId}
            onAssigned={async () => {
              const updated = await demoService.getCandidates();
              setCandidates(updated);
              setSuccessMsg('Assessment assigned successfully!');
            }}
          />
        </section>
      </div>
    </>
  );
}

function ManualAssign({ selectedAssessmentId, onAssigned }: { selectedAssessmentId: string; onAssigned: () => void }) {
  const [email, setEmail] = useState('intern@test.com');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssessmentId) { setError('Please select an assessment first.'); return; }
    setIsLoading(true);
    setError('');
    try {
      await demoService.assignAssessment(selectedAssessmentId, email);
      onAssigned();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleAssign} className="flex gap-sm items-start flex-wrap">
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="intern@test.com"
        className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary outline-none bg-surface-container-lowest"
        required
      />
      <button
        type="submit"
        disabled={isLoading || !selectedAssessmentId}
        className="bg-primary-container text-on-primary px-md py-xs rounded hover:bg-primary transition-colors disabled:opacity-50 font-navigation text-navigation"
      >
        {isLoading ? 'Assigning...' : 'Assign'}
      </button>
      {error && <p className="text-error text-sm w-full">{error}</p>}
    </form>
  );
}
