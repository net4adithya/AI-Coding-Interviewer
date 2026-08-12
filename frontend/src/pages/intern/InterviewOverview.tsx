import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { assessmentsService, AssessmentResponse } from '../../services/assessments';

export function InterviewOverview() {
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    assessmentsService.getMyAssessment()
      .then(data => setAssessment(data))
      .catch(err => console.error("Failed to fetch assignment:", err))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <div className="p-xl text-secondary">Loading your assessment...</div>;
  }

  if (!assessment) {
    return (
      <div className="p-xl">
        <h2 className="font-section-heading text-section-heading mb-xs">No Assessment Assigned</h2>
        <p className="text-secondary">You do not have any active technical coding interviews assigned to you at this time.</p>
      </div>
    );
  }

  return (
    <>
      {/* Assessment Overview Card */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-lg shadow-sm w-full">
        <div className="mb-lg border-b border-outline-variant pb-md">
          <h3 className="font-section-heading text-section-heading text-on-surface mb-xs">{assessment.title}</h3>
          <p className="font-body-main text-body-main text-secondary">Software Development Internship</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-lg">
          {/* Metric: Duration */}
          <div className="flex flex-col">
            <span className="font-metadata text-metadata text-secondary mb-xs flex items-center gap-xs uppercase tracking-wider">
              <span className="material-symbols-outlined text-[16px]">schedule</span>
              Duration
            </span>
            <span className="font-card-title text-card-title text-on-surface">{assessment.duration_minutes} minutes</span>
          </div>
          {/* Metric: Questions */}
          <div className="flex flex-col">
            <span className="font-metadata text-metadata text-secondary mb-xs flex items-center gap-xs uppercase tracking-wider">
              <span className="material-symbols-outlined text-[16px]">list_alt</span>
              Questions
            </span>
            <span className="font-card-title text-card-title text-on-surface">{assessment.total_questions}</span>
          </div>
          {/* Metric: Topics */}
          <div className="flex flex-col col-span-2 md:col-span-1">
            <span className="font-metadata text-metadata text-secondary mb-xs flex items-center gap-xs uppercase tracking-wider">
              <span className="material-symbols-outlined text-[16px]">category</span>
              Topics
            </span>
            <span className="font-card-title text-card-title text-on-surface">
              {assessment.topic_tags?.length ? assessment.topic_tags.join(', ') : 'Mixed'}
            </span>
          </div>
          {/* Metric: Status */}
          <div className="flex flex-col col-span-2 md:col-span-1">
            <span className="font-metadata text-metadata text-secondary mb-xs flex items-center gap-xs uppercase tracking-wider">
              <span className="material-symbols-outlined text-[16px]">info</span>
              Status
            </span>
            <span className="font-card-title text-card-title text-on-surface flex items-center gap-xs">
              <span className="w-2 h-2 rounded-full bg-secondary-fixed-dim"></span>
              Not Started
            </span>
          </div>
        </div>
      </div>

      {/* Content Grid: Before you begin & Rules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-lg mt-md">
        {/* Before you begin */}
        <div className="flex flex-col gap-md bg-surface-container-low border border-surface-variant p-lg rounded-DEFAULT">
          <h4 className="font-section-heading text-section-heading text-on-surface flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary">flag</span>
            Before you begin
          </h4>
          <ul className="flex flex-col gap-sm">
            <li className="flex items-start gap-md">
              <span className="font-code-snippet text-code-snippet text-primary-container bg-surface-container-lowest border border-outline-variant rounded-full w-6 h-6 flex items-center justify-center shrink-0">01</span>
              <span className="font-body-main text-body-main text-on-surface-variant mt-1">You will receive coding problems one at a time.</span>
            </li>
            <li className="flex items-start gap-md">
              <span className="font-code-snippet text-code-snippet text-primary-container bg-surface-container-lowest border border-outline-variant rounded-full w-6 h-6 flex items-center justify-center shrink-0">02</span>
              <span className="font-body-main text-body-main text-on-surface-variant mt-1">Write and test your solution in the coding workspace.</span>
            </li>
            <li className="flex items-start gap-md">
              <span className="font-code-snippet text-code-snippet text-primary-container bg-surface-container-lowest border border-outline-variant rounded-full w-6 h-6 flex items-center justify-center shrink-0">03</span>
              <span className="font-body-main text-body-main text-on-surface-variant mt-1">Your code will be evaluated automatically against test cases.</span>
            </li>
            <li className="flex items-start gap-md">
              <span className="font-code-snippet text-code-snippet text-primary-container bg-surface-container-lowest border border-outline-variant rounded-full w-6 h-6 flex items-center justify-center shrink-0">04</span>
              <span className="font-body-main text-body-main text-on-surface-variant mt-1">Your progress is saved automatically during the interview.</span>
            </li>
            <li className="flex items-start gap-md">
              <span className="font-code-snippet text-code-snippet text-primary-container bg-surface-container-lowest border border-outline-variant rounded-full w-6 h-6 flex items-center justify-center shrink-0">05</span>
              <span className="font-body-main text-body-main text-on-surface-variant mt-1">Once you submit the interview, you cannot make further changes.</span>
            </li>
          </ul>
        </div>
        
        {/* Interview Rules */}
        <div className="flex flex-col gap-md border border-outline-variant p-lg rounded-DEFAULT">
          <h4 className="font-section-heading text-section-heading text-on-surface flex items-center gap-sm">
            <span className="material-symbols-outlined text-secondary">gavel</span>
            Interview rules
          </h4>
          <ul className="list-disc list-inside text-secondary flex flex-col gap-sm font-body-main text-body-main">
            <li>The interview has a fixed time limit.</li>
            <li>Do not refresh or close the interview window unnecessarily.</li>
            <li>Your code is evaluated automatically.</li>
            <li>Hidden test cases are not visible.</li>
            <li>Submit only when you are ready to finish.</li>
          </ul>
        </div>
      </div>

      {/* Start Area */}
      <div className="mt-auto pt-xl border-t border-outline-variant flex flex-col md:flex-row justify-between items-center md:items-end gap-md">
        <div className="text-center md:text-left">
          <h4 className="font-section-heading text-section-heading text-on-surface mb-xs">Ready to begin?</h4>
          <p className="font-body-main text-body-main text-secondary">Once you start, the interview timer will begin.</p>
        </div>
        <Link 
          to="/intern/interview/workspace"
          className="bg-primary-container text-on-primary font-navigation text-navigation px-lg py-sm rounded-DEFAULT flex items-center gap-sm hover:bg-primary transition-colors focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
        >
          Start interview
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </Link>
      </div>
    </>
  );
}
