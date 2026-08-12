import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../services/api';

export function ReviewInterview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [decision, setDecision] = useState<string | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [reviewData, setReviewData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.get(`/authority-review/${id}`)
        .then(res => {
          setReviewData(res.data);
          setDecision(res.data.authority_review?.decision || null);
          setNotes(res.data.authority_review?.internal_notes || '');
        })
        .catch(err => console.error("Failed to fetch review data", err))
        .finally(() => setIsLoading(false));
    }
  }, [id]);

  const handleSave = async () => {
    if (decision && id) {
      try {
        let endpoint = `/authority-review/${id}/approve`;
        if (decision === 'Needs Review') endpoint = `/authority-review/${id}/resubmit`;
        if (decision === 'Not Recommended') endpoint = `/authority-review/${id}/reject`;

        await api.post(endpoint, { internal_notes: notes });
        alert("Decision saved successfully");
        navigate('/authority/interviews');
      } catch (err) {
        console.error("Failed to save decision", err);
        alert("Failed to save decision");
      }
    } else {
      navigate('/authority/interviews');
    }
  };

  if (isLoading) return <div className="p-xl text-secondary">Loading review...</div>;
  if (!reviewData) return <div className="p-xl text-secondary">Review not found or no submission available.</div>;

  const { submission, ai_review, static_analysis, docker_execution, authority_review } = reviewData;

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
  };

  const getOverallResult = () => {
    if (ai_review?.recommendation) return ai_review.recommendation;
    if (ai_review?.overall_score > 80) return "Strong";
    if (ai_review?.overall_score > 60) return "Average";
    return "Needs Improvement";
  };

  return (
    <div className="max-w-max_content_width mx-auto p-xl">
      {/* Page Header */}
      <div className="mb-lg flex justify-between items-end">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface">Interview Review</h1>
        </div>
        <div className="flex items-center gap-sm">
          <span className="font-metadata text-metadata text-on-surface-variant">Status:</span>
          <span className={`inline-flex items-center gap-base px-sm py-xs rounded text-xs font-semibold uppercase tracking-wider ${
            authority_review.status === 'COMPLETED' ? 'bg-surface-container-low border border-primary-fixed-dim text-primary' : 'bg-surface-container border border-outline-variant text-secondary'
          }`}>
            <span className={`w-2 h-2 rounded-full ${authority_review.status === 'COMPLETED' ? 'bg-primary-container' : 'bg-outline'}`}></span>
            {authority_review.status || 'PENDING'}
          </span>
        </div>
      </div>

      {/* Candidate Summary Card */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded p-lg mb-lg flex items-center justify-between">
        <div className="flex items-center gap-lg">
          <div className="w-16 h-16 rounded-full bg-surface-container flex items-center justify-center border border-outline-variant">
            <span className="material-symbols-outlined text-on-surface-variant" style={{ fontSize: '40px' }}>person</span>
          </div>
          <div>
            <h2 className="font-card-title text-card-title text-on-surface">{submission.intern_name || submission.intern_email?.split('@')[0] || 'Unknown'}</h2>
            <p className="font-metadata text-metadata text-on-surface-variant mt-base">{submission.assignment_title}</p>
          </div>
        </div>
        <div className="flex gap-xl">
          <div>
            <p className="font-metadata text-metadata text-on-surface-variant mb-base">Submitted On</p>
            <p className="text-body-main font-medium">{submission.submission_timestamp ? formatDate(submission.submission_timestamp) : 'N/A'}</p>
          </div>
          <div>
            <p className="font-metadata text-metadata text-on-surface-variant mb-base">Language</p>
            <p className="text-body-main font-medium">{submission.language || 'Python 3'}</p>
          </div>
          <div>
            <p className="font-metadata text-metadata text-on-surface-variant mb-base">Overall Result</p>
            <p className="text-body-main font-medium text-primary">{getOverallResult()}</p>
          </div>
        </div>
      </div>

      {/* Performance Overview Row */}
      <div className="grid grid-cols-4 gap-md mb-xl border-b border-outline-variant pb-lg">
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded flex flex-col justify-center">
          <span className="font-metadata text-metadata text-on-surface-variant">Maintainability</span>
          <span className="font-section-heading text-section-heading text-on-surface mt-sm">{static_analysis?.maintainability_index || 'N/A'}</span>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded flex flex-col justify-center">
          <span className="font-metadata text-metadata text-on-surface-variant">Cyclomatic Complexity</span>
          <span className="font-section-heading text-section-heading text-on-surface mt-sm">{static_analysis?.cyclomatic_complexity || 'N/A'}</span>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded flex flex-col justify-center">
          <span className="font-metadata text-metadata text-on-surface-variant">Avg Execution</span>
          <span className="font-section-heading text-section-heading text-on-surface mt-sm">{docker_execution?.execution_time_ms ? `${(docker_execution.execution_time_ms / 1000).toFixed(2)}s` : 'N/A'}</span>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded flex flex-col justify-center">
          <span className="font-metadata text-metadata text-on-surface-variant">Code Smells</span>
          <span className="font-section-heading text-section-heading text-on-surface mt-sm text-primary">{static_analysis?.code_smells || 0}</span>
        </div>
      </div>

      <section className="mb-xl">
        <h3 className="font-section-heading text-section-heading text-on-surface mb-md">Code Analysis</h3>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-lg">
          <div className="flex flex-col gap-sm">
            {(static_analysis?.structured_output?.issues || []).map((issue: any, idx: number) => (
              <div key={idx} className="p-md border border-outline-variant rounded flex items-start gap-md">
                <span className="material-symbols-outlined text-tertiary mt-xs">info</span>
                <div>
                  <p className="text-body-main font-semibold">{issue.type || 'Issue'}</p>
                  <p className="text-metadata text-on-surface-variant">{issue.description || 'Details unavailable'}</p>
                </div>
              </div>
            ))}
            {!static_analysis?.structured_output?.issues?.length && (
              <p className="text-secondary text-sm">No code analysis issues detected.</p>
            )}
          </div>
        </div>
      </section>

      <section className="mb-xl">
        <h3 className="font-section-heading text-section-heading text-on-surface mb-md">Gemini AI Review</h3>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-lg">
          <div className="flex justify-between items-center mb-lg">
            <div>
              <span className="text-metadata text-on-surface-variant">Overall Technical Assessment</span>
              <div className="text-page-title font-bold text-primary">{ai_review?.recommendation || 'Pending'}</div>
            </div>
          </div>
          <div className="mb-md">
            <h4 className="font-card-title text-card-title text-on-surface mb-xs">Strengths</h4>
            <ul className="list-disc ml-md text-body-main text-on-surface-variant">
              {(ai_review?.strengths || []).map((str: string, i: number) => <li key={i}>{str}</li>)}
            </ul>
            {!(ai_review?.strengths?.length) && <span className="text-secondary text-sm">No specific strengths highlighted.</span>}
          </div>
          <div className="mb-md">
            <h4 className="font-card-title text-card-title text-on-surface mb-xs">Weaknesses</h4>
            <ul className="list-disc ml-md text-body-main text-on-surface-variant">
              {(ai_review?.weaknesses || []).map((wk: string, i: number) => <li key={i}>{wk}</li>)}
            </ul>
            {!(ai_review?.weaknesses?.length) && <span className="text-secondary text-sm">No specific weaknesses highlighted.</span>}
          </div>
          <p className="text-metadata text-on-surface-variant italic mt-md">AI-generated analysis is provided as decision support. Final evaluation remains with the interview team.</p>
        </div>
      </section>

      <section className="mb-xl">
        <h3 className="font-section-heading text-section-heading text-on-surface mb-md">Authority Decision</h3>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-lg">
          <div className="flex gap-md mb-lg">
            <button 
              onClick={() => setDecision('Recommended')}
              className={`flex-1 py-sm border rounded font-navigation text-navigation transition-colors ${decision === 'Recommended' ? 'bg-primary text-on-primary border-primary' : 'border-outline-variant hover:bg-surface-container-low text-on-surface'}`}
            >
              Recommended
            </button>
            <button 
              onClick={() => setDecision('Needs Review')}
              className={`flex-1 py-sm border rounded font-navigation text-navigation transition-colors ${decision === 'Needs Review' ? 'bg-secondary text-on-secondary border-secondary' : 'border-outline-variant hover:bg-surface-container-low text-on-surface'}`}
            >
              Needs Review
            </button>
            <button 
              onClick={() => setDecision('Not Recommended')}
              className={`flex-1 py-sm border rounded font-navigation text-navigation transition-colors ${decision === 'Not Recommended' ? 'bg-error text-on-error border-error' : 'border-outline-variant hover:bg-surface-container-low text-on-surface'}`}
            >
              Not Recommended
            </button>
          </div>
          <div className="mb-lg">
            <label className="block text-metadata text-on-surface-variant mb-xs">Internal Notes</label>
            <textarea 
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-outline-variant rounded p-md text-body-main focus:ring-1 focus:ring-primary outline-none bg-surface-container-lowest" 
              placeholder="Add notes for the interview team..." 
              rows={4}
            ></textarea>
          </div>
          <div className="flex justify-end">
            <button onClick={handleSave} className="bg-primary text-on-primary px-xl py-sm rounded font-navigation text-navigation hover:opacity-90 transition-opacity">Save Review</button>
          </div>
        </div>
      </section>
    </div>
  );
}
