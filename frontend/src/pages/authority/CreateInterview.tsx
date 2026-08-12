import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { assessmentsService } from '../../services/assessments';
import { questionBanksService, QuestionBank } from '../../services/questionBanks';

export function CreateInterview() {
  const navigate = useNavigate();
  const [banks, setBanks] = useState<QuestionBank[]>([]);
  const [bankQuestions, setBankQuestions] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);

  // Form State
  const [title, setTitle] = useState('');
  const [bankId, setBankId] = useState<string>('');
  const [duration, setDuration] = useState(60);
  const [numQuestions, setNumQuestions] = useState(5);
  const [topic, setTopic] = useState('All');
  const [language, setLanguage] = useState('All');
  const [diffEasy, setDiffEasy] = useState(2);
  const [diffMed, setDiffMed] = useState(2);
  const [diffHard, setDiffHard] = useState(1);
  const [aiSelection, setAiSelection] = useState(true);
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    questionBanksService.getQuestionBanks().then(data => {
      const completed = data.filter(b => b.status === 'COMPLETED');
      setBanks(completed);
      if (completed.length > 0) {
        setBankId(completed[0].id.toString());
      }
    }).catch(err => console.error("Failed to load banks", err));
  }, []);

  useEffect(() => {
    if (bankId) {
      questionBanksService.getQuestions(parseInt(bankId))
        .then(data => setBankQuestions(data))
        .catch(err => console.error("Failed to load bank questions", err));
    } else {
      setBankQuestions([]);
    }
  }, [bankId]);

  const toggleQuestion = (id: number) => {
    const next = new Set(selectedQuestionIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedQuestionIds(next);
  };

  const totalSelected = aiSelection ? (diffEasy + diffMed + diffHard) : selectedQuestionIds.size;

  const handleCreate = async () => {
    if (!title) {
      alert('Please enter an assessment title.');
      return;
    }
    if (totalSelected === 0) {
      alert('Please select at least 1 question (or configure difficulty distribution for AI).');
      return;
    }
    
    try {
      setIsCreating(true);
      const reqData = {
        title,
        duration_minutes: duration,
        total_questions: totalSelected,
        difficulty_distribution: (aiSelection ? {
          'EASY': diffEasy,
          'MEDIUM': diffMed,
          'HARD': diffHard
        } : {}) as Record<string, number>,
        topic_tags: topic !== 'All' ? [topic] : [],
        ai_selection_enabled: aiSelection,
        question_ids: aiSelection ? undefined : Array.from(selectedQuestionIds),
        question_bank_id: bankId ? parseInt(bankId) : undefined,
      };

      // Create Assessment
      const assessment = await assessmentsService.createAssessment(reqData);
      
      if (aiSelection) {
        // Generate Questions
        await assessmentsService.generateAssessment(assessment.id);
      }

      // We explicitly DO NOT publish it yet. It stays in GENERATED/DRAFT state.
      navigate('/authority/interviews');
    } catch (error) {
      console.error('Failed to create assessment:', error);
      alert('Failed to create assessment. See console for details.');
    } finally {
      setIsCreating(false);
    }
  };

  const getTopicsFromBank = () => {
    const topics = new Set<string>();
    bankQuestions.forEach(q => {
      if (q.topic) topics.add(q.topic);
    });
    return Array.from(topics);
  };

  return (
    <div className="w-full max-w-max_content_width px-xl py-xl flex flex-col gap-lg mx-auto">
      {/* Breadcrumb & Header */}
      <div className="flex flex-col gap-sm">
        <div className="font-metadata text-metadata text-secondary flex items-center gap-xs">
          <Link to="/authority/interviews" className="hover:text-primary transition-colors">Assessments</Link>
          <span>/</span>
          <span className="text-on-surface-variant">Create Assessment</span>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="font-page-title text-page-title text-on-surface">Create assessment</h1>
          <div className="flex gap-md">
            <button className="bg-transparent border border-outline-variant text-on-surface px-md py-xs rounded hover:bg-surface-container-high transition-colors font-navigation text-navigation">Save draft</button>
            <button 
              onClick={handleCreate} 
              disabled={isCreating}
              className="bg-primary-container text-on-primary px-md py-xs rounded hover:opacity-90 transition-opacity font-navigation text-navigation disabled:opacity-50"
            >
              {isCreating ? 'Creating...' : 'Create Assessment'}
            </button>
          </div>
        </div>
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-lg items-start">
        {/* Left Column (Form) */}
        <div className="lg:col-span-8 flex flex-col gap-lg">
          {/* Assessment details */}
          <section className="bg-surface-container-lowest border border-outline-variant rounded p-md flex flex-col gap-md">
            <h2 className="font-card-title text-card-title text-on-surface border-b border-outline-variant pb-xs">Assessment details</h2>
            <div className="flex flex-col gap-sm">
              <label className="font-navigation text-navigation text-on-surface" htmlFor="assessment-title">Assessment title</label>
              <input 
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest" 
                id="assessment-title" 
                placeholder="Enter assessment title" 
                type="text" 
              />
            </div>
            <div className="flex flex-col gap-sm">
              <label className="font-navigation text-navigation text-on-surface" htmlFor="question-bank">Question bank</label>
              <select 
                value={bankId}
                onChange={e => setBankId(e.target.value)}
                className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest appearance-none" 
                id="question-bank"
              >
                {banks.map(b => (
                  <option key={b.id} value={b.id.toString()}>{b.filename} ({b.question_count} questions)</option>
                ))}
              </select>
            </div>
          </section>

          {/* Settings & Topics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
            <section className="bg-surface-container-lowest border border-outline-variant rounded p-md flex flex-col gap-md">
              <h2 className="font-card-title text-card-title text-on-surface border-b border-outline-variant pb-xs">Settings</h2>
              <div className="flex flex-col gap-sm">
                <label className="font-navigation text-navigation text-on-surface" htmlFor="duration">Duration (minutes)</label>
                <input 
                  value={duration}
                  onChange={e => setDuration(parseInt(e.target.value) || 0)}
                  className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest" 
                  id="duration" min="15" step="15" type="number" 
                />
              </div>
              {aiSelection && (
                <div className="flex flex-col gap-sm">
                  <label className="font-navigation text-navigation text-on-surface" htmlFor="num-questions">Target number of questions</label>
                  <input 
                    value={numQuestions}
                    onChange={e => setNumQuestions(parseInt(e.target.value) || 0)}
                    className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest" 
                    id="num-questions" min="1" type="number" 
                  />
                </div>
              )}
            </section>
            
            <section className="bg-surface-container-lowest border border-outline-variant rounded p-md flex flex-col gap-md">
              <h2 className="font-card-title text-card-title text-on-surface border-b border-outline-variant pb-xs">Topics &amp; Language</h2>
              <div className="flex flex-col gap-sm">
                <label className="font-navigation text-navigation text-on-surface" htmlFor="topic">Topic</label>
                <select 
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                  className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest appearance-none" 
                  id="topic"
                >
                  <option value="All">All Topics</option>
                  {getTopicsFromBank().map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-sm">
                <label className="font-navigation text-navigation text-on-surface" htmlFor="language">Programming language</label>
                <select 
                  value={language}
                  onChange={e => setLanguage(e.target.value)}
                  className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest appearance-none" 
                  id="language"
                >
                  <option value="All">All</option>
                  <option value="Python">Python</option>
                  <option value="Java">Java</option>
                  <option value="C++">C++</option>
                </select>
              </div>
            </section>
          </div>

          {/* Question Selection Mode */}
          <section className="bg-surface-container-lowest border border-outline-variant rounded p-md flex flex-col gap-md">
            <h2 className="font-card-title text-card-title text-on-surface border-b border-outline-variant pb-xs">Question selection</h2>
            <label className="flex items-start gap-sm cursor-pointer group mb-sm">
              <div className="relative flex items-center justify-center w-5 h-5 mt-0.5">
                <input 
                  checked={aiSelection}
                  onChange={e => setAiSelection(e.target.checked)}
                  className="appearance-none w-4 h-4 border border-outline-variant rounded checked:bg-primary checked:border-primary transition-colors peer" 
                  type="checkbox" 
                />
                <span className="material-symbols-outlined text-[14px] text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity">check</span>
              </div>
              <div className="flex flex-col">
                <span className="font-navigation text-navigation text-on-surface group-hover:text-primary transition-colors">AI-assisted selection</span>
                <span className="font-metadata text-metadata text-secondary">Gemini will select a suitable combination of questions based on your topic, difficulty and duration requirements.</span>
              </div>
            </label>

            {aiSelection ? (
              <div className="flex flex-col gap-md border-t border-outline-variant pt-sm mt-sm">
                <p className="font-metadata text-metadata text-secondary">Choose how many questions of each difficulty should appear.</p>
                <div className="grid grid-cols-3 gap-md">
                  <div className="flex flex-col gap-xs">
                    <label className="font-navigation text-navigation text-on-surface flex items-center justify-between" htmlFor="diff-easy">Easy</label>
                    <input 
                      value={diffEasy}
                      onChange={e => setDiffEasy(parseInt(e.target.value) || 0)}
                      className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest text-center" 
                      id="diff-easy" min="0" type="number" 
                    />
                  </div>
                  <div className="flex flex-col gap-xs">
                    <label className="font-navigation text-navigation text-on-surface flex items-center justify-between" htmlFor="diff-med">Medium</label>
                    <input 
                      value={diffMed}
                      onChange={e => setDiffMed(parseInt(e.target.value) || 0)}
                      className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest text-center" 
                      id="diff-med" min="0" type="number" 
                    />
                  </div>
                  <div className="flex flex-col gap-xs">
                    <label className="font-navigation text-navigation text-on-surface flex items-center justify-between" htmlFor="diff-hard">Hard</label>
                    <input 
                      value={diffHard}
                      onChange={e => setDiffHard(parseInt(e.target.value) || 0)}
                      className="border border-outline-variant rounded px-sm py-xs text-body-main focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors w-full bg-surface-container-lowest text-center" 
                      id="diff-hard" min="0" type="number" 
                    />
                  </div>
                </div>
                <div className="pt-sm border-t border-outline-variant flex justify-between items-center">
                  <span className="font-navigation text-navigation text-on-surface">Total questions selected:</span>
                  <span className={`font-section-heading text-section-heading ${totalSelected === numQuestions ? 'text-primary' : 'text-amber-600'}`}>{totalSelected}</span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-md border-t border-outline-variant pt-sm mt-sm">
                <p className="font-metadata text-metadata text-secondary">Manually select questions from the chosen bank.</p>
                <div className="max-h-64 overflow-y-auto flex flex-col gap-xs border border-outline-variant rounded p-xs">
                  {bankQuestions.map(q => (
                    <label key={q.id} className="flex items-start gap-sm cursor-pointer p-xs hover:bg-surface-container-low rounded">
                      <div className="relative flex items-center justify-center w-5 h-5 mt-0.5">
                        <input 
                          checked={selectedQuestionIds.has(q.id)}
                          onChange={() => toggleQuestion(q.id)}
                          className="appearance-none w-4 h-4 border border-outline-variant rounded checked:bg-primary checked:border-primary transition-colors peer" 
                          type="checkbox" 
                        />
                        <span className="material-symbols-outlined text-[14px] text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity">check</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="font-navigation text-navigation text-on-surface">{q.title}</span>
                        <span className="font-metadata text-metadata text-secondary">
                          {q.difficulty} • {q.topic} • {q.expected_time_minutes} min
                        </span>
                      </div>
                    </label>
                  ))}
                  {bankQuestions.length === 0 && (
                    <div className="text-secondary text-center p-sm">No questions found in this bank.</div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Right Column (Summary) */}
        <div className="lg:col-span-4 sticky top-xl">
          <div className="bg-surface-container-lowest border border-outline-variant rounded flex flex-col shadow-sm">
            <div className="p-md border-b border-outline-variant bg-surface-container-high rounded-t">
              <h2 className="font-section-heading text-section-heading text-on-surface">Assessment summary</h2>
            </div>
            <div className="p-md flex flex-col gap-md font-body-main text-on-surface">
              <div className="flex justify-between border-b border-outline-variant pb-sm">
                <span className="text-secondary">Question bank</span>
                <span className="font-medium text-right max-w-[60%] truncate">
                  {banks.find(b => b.id.toString() === bankId)?.filename || 'None selected'}
                </span>
              </div>
              <div className="flex justify-between border-b border-outline-variant pb-sm">
                <span className="text-secondary">Questions</span>
                <span className="font-medium">{totalSelected}</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant pb-sm">
                <span className="text-secondary">Duration</span>
                <span className="font-medium">{duration} minutes</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant pb-sm">
                <span className="text-secondary">Topic</span>
                <span className="font-medium">{topic}</span>
              </div>
              {aiSelection && (
                <div className="flex justify-between border-b border-outline-variant pb-sm">
                  <span className="text-secondary">Difficulty</span>
                  <span className="font-medium">{diffEasy}E, {diffMed}M, {diffHard}H</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-secondary">Language</span>
                <span className="font-medium">{language}</span>
              </div>
            </div>
            <div className="p-md bg-surface border-t border-outline-variant rounded-b flex flex-col gap-xs font-metadata text-metadata text-center">
              <span className="text-primary font-medium">{totalSelected} questions will be {aiSelection ? 'selected' : 'included'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
