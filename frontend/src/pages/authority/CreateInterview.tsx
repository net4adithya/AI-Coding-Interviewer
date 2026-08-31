// frontend/src/pages/authority/CreateInterview.tsx
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { demoService } from '../../services/demoApi';
import { questionBanksService } from '../../services/questionBanks';

const LANGUAGES = ['Python', 'Java', 'C++', 'JavaScript', 'Other'];

type WorkflowStep = 'details' | 'selection' | 'gemini_review';

interface BankQuestion {
  id: string;
  title: string;
  difficulty: string;
  topic: string;
  problem_statement: string;
  constraints?: string;
  input_format?: string;
  output_format?: string;
  examples?: any[];
  test_cases?: any[];
}

interface QuestionBankItem {
  id: string | number;
  title?: string;
  filename?: string;
  topic?: string;
  questions?: BankQuestion[];
}

export function CreateInterview() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('details');

  // Form Fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState<number | ''>(60);
  const [language, setLanguage] = useState('Python');
  const [customLanguage, setCustomLanguage] = useState('');
  const [topic] = useState('Algorithms');

  // Question Banks State
  const [banks, setBanks] = useState<QuestionBankItem[]>([]);
  const [selectedBankId, setSelectedBankId] = useState<string | number>('');
  const [bankQuestions, setBankQuestions] = useState<BankQuestion[]>([]);
  const [isLoadingBanks, setIsLoadingBanks] = useState(true);

  // Distribution Requested
  const [reqEasy, setReqEasy] = useState(2);
  const [reqMed, setReqMed] = useState(2);
  const [reqHard, setReqHard] = useState(1);

  // Question Selection
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Gemini Confirmation Review
  const [geminiReview, setGeminiReview] = useState<any>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Effective programming language
  const finalLanguage = language === 'Other' ? (customLanguage.trim() || 'Other') : language;

  // Normalize difficulty string to 'Easy' | 'Medium' | 'Hard'
  const normDiff = (d: string = ''): 'Easy' | 'Medium' | 'Hard' => {
    const upper = d.toUpperCase();
    if (upper === 'EASY') return 'Easy';
    if (upper === 'HARD') return 'Hard';
    return 'Medium';
  };

  // Available questions in selected bank grouped by normalized difficulty
  const availableEasyQuestions = bankQuestions.filter(q => normDiff(q.difficulty) === 'Easy');
  const availableMedQuestions = bankQuestions.filter(q => normDiff(q.difficulty) === 'Medium');
  const availableHardQuestions = bankQuestions.filter(q => normDiff(q.difficulty) === 'Hard');

  const maxEasy = availableEasyQuestions.length;
  const maxMed = availableMedQuestions.length;
  const maxHard = availableHardQuestions.length;

  const totalReq = reqEasy + reqMed + reqHard;

  // Selected counts by difficulty
  const selectedQuestions = bankQuestions.filter(q => selectedIds.includes(q.id));
  const selectedEasyCount = selectedQuestions.filter(q => normDiff(q.difficulty) === 'Easy').length;
  const selectedMedCount = selectedQuestions.filter(q => normDiff(q.difficulty) === 'Medium').length;
  const selectedHardCount = selectedQuestions.filter(q => normDiff(q.difficulty) === 'Hard').length;

  const isSelectionValid =
    selectedEasyCount === reqEasy &&
    selectedMedCount === reqMed &&
    selectedHardCount === reqHard &&
    selectedQuestions.length > 0;

  // Load Question Banks on mount
  useEffect(() => {
    console.log('[DEMO PIPELINE] CREATE_ASSIGNMENT -> Mount');
    fetchQuestionBanks();
  }, []);

  const fetchQuestionBanks = async () => {
    try {
      setIsLoadingBanks(true);
      const bankList = await questionBanksService.getQuestionBanks();
      setBanks(bankList || []);
      if (bankList && bankList.length > 0) {
        handleSelectBank(bankList[0].id);
      }
    } catch (err: any) {
      console.error('[DEMO PIPELINE] Failed to load question banks:', err);
    } finally {
      setIsLoadingBanks(false);
    }
  };

  const handleSelectBank = async (bankId: string | number) => {
    setSelectedBankId(bankId);
    try {
      const fullBank = await questionBanksService.getQuestionBank(bankId);
      const qList: BankQuestion[] = fullBank.questions || [];
      setBankQuestions(qList);

      const eCount = qList.filter(q => normDiff(q.difficulty) === 'Easy').length;
      const mCount = qList.filter(q => normDiff(q.difficulty) === 'Medium').length;
      const hCount = qList.filter(q => normDiff(q.difficulty) === 'Hard').length;

      setReqEasy(Math.min(2, eCount));
      setReqMed(Math.min(2, mCount));
      setReqHard(Math.min(1, hCount));

      // Default auto-select requested count
      const autoSelected = [
        ...qList.filter(q => normDiff(q.difficulty) === 'Easy').slice(0, Math.min(2, eCount)),
        ...qList.filter(q => normDiff(q.difficulty) === 'Medium').slice(0, Math.min(2, mCount)),
        ...qList.filter(q => normDiff(q.difficulty) === 'Hard').slice(0, Math.min(1, hCount)),
      ].map(q => q.id);

      setSelectedIds(autoSelected);
    } catch (err: any) {
      console.error('[DEMO PIPELINE] Error fetching bank detail:', err);
    }
  };

  const handleProceedToSelection = () => {
    if (!title.trim()) {
      alert('Please enter an assessment title.');
      return;
    }
    if (!duration || duration < 1 || duration > 300) {
      alert('Please enter a valid duration between 1 and 300 minutes.');
      return;
    }
    if (language === 'Other' && !customLanguage.trim()) {
      alert('Please specify the language name.');
      return;
    }
    if (totalReq === 0) {
      alert('Please request at least 1 question.');
      return;
    }
    if (!selectedBankId) {
      alert('Please select a Question Bank.');
      return;
    }

    // Refresh selected IDs matching requested numbers
    const autoSelected = [
      ...availableEasyQuestions.slice(0, reqEasy),
      ...availableMedQuestions.slice(0, reqMed),
      ...availableHardQuestions.slice(0, reqHard),
    ].map(q => q.id);

    setSelectedIds(autoSelected);
    setCurrentStep('selection');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleToggleQuestion = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleRunGeminiReview = async () => {
    if (!isSelectionValid) {
      alert('Please select the exact number of Easy, Medium, and Hard questions requested.');
      return;
    }

    setIsReviewing(true);
    setErrorMsg('');
    try {
      console.log('[DEMO PIPELINE] GEMINI_CONFIRM -> Requesting Gemini review of selected questions');
      const review = await demoService.reviewSelection({
        title,
        description,
        duration_minutes: typeof duration === 'number' ? duration : 60,
        language: finalLanguage,
        topic,
        selected_questions: selectedQuestions,
      });
      setGeminiReview(review);
      setCurrentStep('gemini_review');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      console.error('[DEMO PIPELINE] Gemini review failed:', err);
      setErrorMsg(err.message || 'Gemini review failed.');
    } finally {
      setIsReviewing(false);
    }
  };

  const handleConfirmAssessment = async () => {
    setIsConfirming(true);
    setErrorMsg('');
    try {
      console.log('[DEMO PIPELINE] CREATE_ASSESSMENT -> Confirming assessment with DemoStore');
      const created = await demoService.confirmAssessment({
        title,
        description,
        duration_minutes: typeof duration === 'number' ? duration : 60,
        language: finalLanguage,
        topic,
        easy_count: reqEasy,
        medium_count: reqMed,
        hard_count: reqHard,
        questions: selectedQuestions,
      });
      console.log('[DEMO PIPELINE] Assessment confirmed:', created);
      navigate(`/authority/candidates?assessmentId=${created.id}`);
    } catch (err: any) {
      console.error('[DEMO PIPELINE] Confirm assessment failed:', err);
      setErrorMsg(err.message || 'Confirm assessment failed.');
    } finally {
      setIsConfirming(false);
    }
  };

  const selectedBankObj = banks.find(b => String(b.id) === String(selectedBankId));

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-24">
      {/* TOP BAR BREADCRUMB HEADER */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10 px-6 py-4 shadow-xs">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
              <Link to="/authority/dashboard" className="hover:text-sky-600">Dashboard</Link>
              <span>/</span>
              <Link to="/authority/question-bank" className="hover:text-sky-600">Question Banks</Link>
              <span>/</span>
              <span className="text-slate-800">Create Assignment</span>
            </div>
            
            {/* HEADING WITH ICON AND SUB-TAGLINE */}
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-sky-600 text-[26px]">fact_check</span>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Create Assessment Assignment
              </h1>
            </div>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Build a coding assessment from your question bank and review it with Gemini AI.
            </p>
          </div>

          {/* STEP INDICATOR PILLS */}
          <div className="flex items-center gap-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => setCurrentStep('details')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 ${
                currentStep === 'details' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <span className="w-4 h-4 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-[10px]">1</span>
              Details & Bank
            </button>

            <button
              onClick={() => {
                if (title && totalReq > 0) setCurrentStep('selection');
              }}
              disabled={!title || totalReq === 0}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 disabled:opacity-40 ${
                currentStep === 'selection' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <span className="w-4 h-4 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-[10px]">2</span>
              Question Selection
            </button>

            <button
              onClick={() => {
                if (geminiReview) setCurrentStep('gemini_review');
              }}
              disabled={!geminiReview}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 disabled:opacity-40 ${
                currentStep === 'gemini_review' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <span className="w-4 h-4 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-[10px]">3</span>
              Gemini Review
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 pt-6">
        {errorMsg && (
          <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm font-semibold flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px]">error</span>
            {errorMsg}
          </div>
        )}

        {/* MAIN WORKFLOW GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT MAIN AREA (~70%) */}
          <div className="lg:col-span-8 flex flex-col gap-6">

            {/* STEP 1: DETAILS & QUESTION BANK SELECTION */}
            {currentStep === 'details' && (
              <>
                {/* 1. ASSESSMENT DETAILS */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
                  <div className="bg-slate-50/80 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <span className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-extrabold text-xs">1</span>
                      Assessment Details
                    </h2>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Step 1 of 3</span>
                  </div>

                  <div className="p-6 flex flex-col gap-5">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Assessment Title <span className="text-rose-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Python Algorithms & Data Structures Assessment"
                        className="w-full h-11 px-4 text-sm font-medium text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Description / Instructions
                      </label>
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={2}
                        placeholder="Brief overview of the skills evaluated in this assessment..."
                        className="w-full p-3 text-sm font-medium text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
                      />
                    </div>

                    {/* DURATION (NUMERIC INPUT) & PROGRAMMING LANGUAGE */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                          Duration (minutes) <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="number"
                          min={1}
                          max={300}
                          value={duration}
                          placeholder="60"
                          onChange={(e) => {
                            const val = e.target.value === '' ? '' : parseInt(e.target.value, 10);
                            setDuration(val === '' ? '' : Math.max(1, Math.min(300, val)));
                          }}
                          className="w-full h-11 px-4 text-sm font-semibold text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                        />
                        <span className="text-[11px] text-slate-400 mt-1 block">Specify test time limit (1 – 300 minutes)</span>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                          Programming Language <span className="text-rose-500">*</span>
                        </label>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full h-11 px-3 text-sm font-semibold text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                        >
                          {LANGUAGES.map((lang) => (
                            <option key={lang} value={lang}>{lang}</option>
                          ))}
                        </select>

                        {/* CUSTOM LANGUAGE INPUT IF 'OTHER' IS SELECTED */}
                        {language === 'Other' && (
                          <div className="mt-3">
                            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                              Specify Other Language <span className="text-rose-500">*</span>
                            </label>
                            <input
                              type="text"
                              value={customLanguage}
                              onChange={(e) => setCustomLanguage(e.target.value)}
                              placeholder="e.g. Rust, Go, C#, TypeScript"
                              className="w-full h-10 px-3 text-sm font-medium text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. QUESTION BANK SELECTION */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
                  <div className="bg-slate-50/80 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-extrabold text-xs">2</span>
                        Select Question Bank
                      </h2>
                      <p className="text-xs text-slate-500 font-medium ml-9 mt-0.5">
                        Choose the PDF question bank for this assessment.
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-sky-700 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-200">
                      PDF Source
                    </span>
                  </div>

                  <div className="p-6 flex flex-col gap-4">
                    {isLoadingBanks ? (
                      <div className="text-sm font-semibold text-slate-500 py-4 text-center">Loading Question Banks...</div>
                    ) : banks.length === 0 ? (
                      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 text-sm font-medium flex items-center justify-between">
                        <span>No Question Banks uploaded yet.</span>
                        <Link to="/authority/question-bank" className="text-sky-700 font-bold hover:underline">
                          + Upload PDF Question Bank →
                        </Link>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-4">
                        <div>
                          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                            Available Question Banks <span className="text-rose-500">*</span>
                          </label>
                          <select
                            value={selectedBankId}
                            onChange={(e) => handleSelectBank(e.target.value)}
                            className="w-full h-11 px-4 text-sm font-bold text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                          >
                            {banks.map((b) => (
                              <option key={b.id} value={b.id}>
                                {b.title || b.filename || 'Question Bank'} ({b.questions?.length || 0} questions available)
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* SELECTED QUESTION BANK DETAILS CARD */}
                        {selectedBankObj && (
                          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div>
                              <h4 className="text-sm font-bold text-slate-900">
                                {selectedBankObj.title || selectedBankObj.filename || 'Question Bank'}
                              </h4>
                              <p className="text-xs text-slate-500 font-medium mt-0.5">
                                Total Questions Available: <strong className="text-slate-800">{bankQuestions.length}</strong>
                              </p>
                            </div>
                            <div className="flex items-center gap-2 text-xs font-bold">
                              <span className="bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-md border border-emerald-200">
                                Easy: {maxEasy}
                              </span>
                              <span className="bg-amber-100 text-amber-800 px-2.5 py-1 rounded-md border border-amber-200">
                                Medium: {maxMed}
                              </span>
                              <span className="bg-rose-100 text-rose-800 px-2.5 py-1 rounded-md border border-rose-200">
                                Hard: {maxHard}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* 3. QUESTION DISTRIBUTION CONTROLS */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
                  <div className="bg-slate-50/80 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <span className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-extrabold text-xs">3</span>
                      Configure Question Distribution
                    </h2>
                    <div className="flex items-center gap-1.5 text-xs font-extrabold text-slate-700 bg-white border border-slate-300 px-3 py-1 rounded-full shadow-2xs">
                      <span>TOTAL:</span>
                      <span className="text-sky-600 text-sm">{totalReq}</span>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                      {/* EASY COUNTER CARD */}
                      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4 flex flex-col items-center">
                        <div className="flex items-center justify-between w-full mb-3">
                          <span className="text-xs font-extrabold text-emerald-800 uppercase tracking-wider">Easy</span>
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                            Max {maxEasy}
                          </span>
                        </div>
                        <div className="flex items-center justify-center gap-3">
                          <button
                            type="button"
                            onClick={() => setReqEasy(Math.max(0, reqEasy - 1))}
                            disabled={reqEasy === 0}
                            className="w-9 h-9 rounded-lg bg-white border border-emerald-300 text-emerald-800 font-extrabold text-lg flex items-center justify-center hover:bg-emerald-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            -
                          </button>
                          <span className="w-10 text-center font-black text-2xl text-emerald-900">{reqEasy}</span>
                          <button
                            type="button"
                            onClick={() => setReqEasy(Math.min(maxEasy, reqEasy + 1))}
                            disabled={reqEasy >= maxEasy}
                            className="w-9 h-9 rounded-lg bg-white border border-emerald-300 text-emerald-800 font-extrabold text-lg flex items-center justify-center hover:bg-emerald-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            +
                          </button>
                        </div>
                      </div>

                      {/* MEDIUM COUNTER CARD */}
                      <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-4 flex flex-col items-center">
                        <div className="flex items-center justify-between w-full mb-3">
                          <span className="text-xs font-extrabold text-amber-800 uppercase tracking-wider">Medium</span>
                          <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                            Max {maxMed}
                          </span>
                        </div>
                        <div className="flex items-center justify-center gap-3">
                          <button
                            type="button"
                            onClick={() => setReqMed(Math.max(0, reqMed - 1))}
                            disabled={reqMed === 0}
                            className="w-9 h-9 rounded-lg bg-white border border-amber-300 text-amber-800 font-extrabold text-lg flex items-center justify-center hover:bg-amber-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            -
                          </button>
                          <span className="w-10 text-center font-black text-2xl text-amber-900">{reqMed}</span>
                          <button
                            type="button"
                            onClick={() => setReqMed(Math.min(maxMed, reqMed + 1))}
                            disabled={reqMed >= maxMed}
                            className="w-9 h-9 rounded-lg bg-white border border-amber-300 text-amber-800 font-extrabold text-lg flex items-center justify-center hover:bg-amber-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            +
                          </button>
                        </div>
                      </div>

                      {/* HARD COUNTER CARD */}
                      <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-4 flex flex-col items-center">
                        <div className="flex items-center justify-between w-full mb-3">
                          <span className="text-xs font-extrabold text-rose-800 uppercase tracking-wider">Hard</span>
                          <span className="text-[10px] font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full">
                            Max {maxHard}
                          </span>
                        </div>
                        <div className="flex items-center justify-center gap-3">
                          <button
                            type="button"
                            onClick={() => setReqHard(Math.max(0, reqHard - 1))}
                            disabled={reqHard === 0}
                            className="w-9 h-9 rounded-lg bg-white border border-rose-300 text-rose-800 font-extrabold text-lg flex items-center justify-center hover:bg-rose-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            -
                          </button>
                          <span className="w-10 text-center font-black text-2xl text-rose-900">{reqHard}</span>
                          <button
                            type="button"
                            onClick={() => setReqHard(Math.min(maxHard, reqHard + 1))}
                            disabled={reqHard >= maxHard}
                            className="w-9 h-9 rounded-lg bg-white border border-rose-300 text-rose-800 font-extrabold text-lg flex items-center justify-center hover:bg-rose-100 transition-colors disabled:opacity-30 shadow-2xs"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* PRIMARY ACTION BUTTON TO PROCEED */}
                    <button
                      type="button"
                      onClick={handleProceedToSelection}
                      disabled={!title.trim() || !duration || duration < 1 || duration > 300 || totalReq === 0 || !selectedBankId || (language === 'Other' && !customLanguage.trim())}
                      className="w-full h-12 bg-sky-600 hover:bg-sky-500 text-white font-bold text-base rounded-xl shadow-md transition-all disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <span>Continue to Question Selection</span>
                      <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* STEP 2: QUESTION SELECTION FROM QUESTION BANK */}
            {currentStep === 'selection' && (
              <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
                <div className="bg-slate-50/80 px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <span className="material-symbols-outlined text-sky-600 text-[20px]">checklist</span>
                      Step 2 — Question Selection
                    </h2>
                    <p className="text-xs text-slate-500 font-medium mt-0.5">
                      Bank: <strong className="text-slate-800">{selectedBankObj?.title || selectedBankObj?.filename || 'Selected Bank'}</strong>
                    </p>
                  </div>

                  {/* LIVE SELECTION COUNTERS */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                      selectedEasyCount === reqEasy ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}>
                      Easy: {selectedEasyCount} / {reqEasy}
                    </span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                      selectedMedCount === reqMed ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}>
                      Medium: {selectedMedCount} / {reqMed}
                    </span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                      selectedHardCount === reqHard ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}>
                      Hard: {selectedHardCount} / {reqHard}
                    </span>
                  </div>
                </div>

                <div className="p-6 flex flex-col gap-6">
                  {/* QUESTION LIST GROUPED BY DIFFICULTY */}
                  {['Easy', 'Medium', 'Hard'].map((diff) => {
                    const diffQs = bankQuestions.filter(q => normDiff(q.difficulty) === diff);
                    if (diffQs.length === 0) return null;

                    const colorClass = diff === 'Easy' ? 'emerald' : diff === 'Medium' ? 'amber' : 'rose';

                    return (
                      <div key={diff} className="flex flex-col gap-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <span className={`text-xs font-extrabold uppercase tracking-wider text-${colorClass}-800`}>
                            {diff} Questions ({diffQs.length} available)
                          </span>
                        </div>

                        <div className="flex flex-col gap-3">
                          {diffQs.map((q) => {
                            const isChecked = selectedIds.includes(q.id);
                            return (
                              <div
                                key={q.id}
                                onClick={() => handleToggleQuestion(q.id)}
                                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-4 ${
                                  isChecked
                                    ? 'bg-sky-50/50 border-sky-300 shadow-2xs'
                                    : 'bg-white border-slate-200 hover:border-slate-300'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => {}}
                                  className="mt-1 w-4 h-4 text-sky-600 rounded focus:ring-sky-500 cursor-pointer"
                                />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <h4 className="text-sm font-bold text-slate-900">{q.title}</h4>
                                    <span className="text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                                      {q.topic || topic}
                                    </span>
                                  </div>
                                  <p className="text-xs text-slate-600 line-clamp-2">{q.problem_statement}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}

                  {/* BOTTOM ACTION BAR */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-200">
                    <button
                      type="button"
                      onClick={() => setCurrentStep('details')}
                      className="px-4 py-2.5 text-sm font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                    >
                      ← Back
                    </button>

                    <button
                      type="button"
                      onClick={handleRunGeminiReview}
                      disabled={!isSelectionValid || isReviewing}
                      className="w-full sm:w-auto px-6 py-3 bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm rounded-xl shadow-md transition-all disabled:opacity-40 flex items-center justify-center gap-2"
                    >
                      {isReviewing ? (
                        <>
                          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                          <span>Gemini Reviewing...</span>
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                          <span>Review with Gemini →</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: GEMINI CONFIRMATION & ASSESSMENT REVIEW */}
            {currentStep === 'gemini_review' && geminiReview && (
              <div className="flex flex-col gap-6">
                {/* GEMINI ASSESSMENT REVIEW CARD */}
                <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-sky-950 text-white rounded-xl p-6 shadow-xl border border-slate-700">
                  <div className="flex items-center gap-2 mb-3 text-sky-400 font-bold text-xs uppercase tracking-wider">
                    <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                    <span>Gemini Assessment Review</span>
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">Assessment Quality & Coverage Review</h3>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-xs">
                    <div className="bg-white/10 rounded-lg p-3 backdrop-blur-xs border border-white/10">
                      <span className="text-slate-400 font-bold block mb-1">QUALITY</span>
                      <p className="text-slate-200 font-medium">{geminiReview.quality_summary}</p>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 backdrop-blur-xs border border-white/10">
                      <span className="text-slate-400 font-bold block mb-1">DIFFICULTY BALANCE</span>
                      <p className="text-slate-200 font-medium">{geminiReview.difficulty_balance}</p>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 backdrop-blur-xs border border-white/10">
                      <span className="text-slate-400 font-bold block mb-1">COVERAGE</span>
                      <p className="text-slate-200 font-medium">{geminiReview.coverage}</p>
                    </div>
                  </div>

                  {geminiReview.recommendations && geminiReview.recommendations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/10 text-xs text-slate-300">
                      <span className="font-bold text-slate-400 uppercase tracking-wider block mb-1">RECOMMENDATIONS</span>
                      <ul className="list-disc list-inside space-y-1">
                        {geminiReview.recommendations.map((rec: string, i: number) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* SELECTED QUESTIONS PREVIEW */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
                  <h3 className="text-base font-bold text-slate-900 mb-4">Confirmed Assessment Questions ({selectedQuestions.length})</h3>
                  <div className="flex flex-col gap-3">
                    {selectedQuestions.map((q, idx) => (
                      <div key={q.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-slate-700">Question {idx + 1}: {q.title}</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider bg-white border border-slate-300 text-slate-700 px-2 py-0.5 rounded">
                            {q.difficulty}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 line-clamp-2">{q.problem_statement}</p>
                      </div>
                    ))}
                  </div>

                  {/* BOTTOM ACTION BAR */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 mt-6 border-t border-slate-200">
                    <button
                      type="button"
                      onClick={() => setCurrentStep('selection')}
                      className="px-4 py-2.5 text-sm font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                    >
                      ← Back to Questions
                    </button>

                    <button
                      type="button"
                      onClick={handleConfirmAssessment}
                      disabled={isConfirming}
                      className="w-full sm:w-auto px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-base rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
                    >
                      {isConfirming ? (
                        <span>Confirming Assessment...</span>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[20px]">check_circle</span>
                          <span>Confirm Assessment →</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT SIDEBAR (~30%): LIVE ASSESSMENT SUMMARY */}
          <div className="lg:col-span-4 sticky top-24">
            <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden flex flex-col">
              <div className="bg-slate-50 px-5 py-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sky-600 text-[18px]">description</span>
                  Assessment Summary
                </h3>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Live</span>
              </div>

              <div className="p-5 flex flex-col gap-4 text-xs font-medium">
                <div>
                  <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Title</span>
                  <span className={`block text-sm font-bold truncate mt-0.5 ${title.trim() ? 'text-slate-900' : 'text-slate-400 italic'}`}>
                    {title.trim() || 'Not set'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-3">
                  <div>
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Duration</span>
                    <span className="block text-sm font-semibold text-slate-800 mt-0.5">
                      {duration ? `${duration} min` : 'Not set'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Language</span>
                    <span className="block text-sm font-semibold text-slate-800 mt-0.5">
                      {finalLanguage}
                    </span>
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Question Bank</span>
                  <span className="block text-xs font-bold text-sky-700 mt-0.5 truncate">
                    {selectedBankObj?.title || selectedBankObj?.filename || 'None selected'}
                  </span>
                </div>

                <div className="border-t border-slate-100 pt-3 flex flex-col gap-1">
                  <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] mb-1">Requested Breakdown</span>
                  <div className="flex justify-between text-slate-700">
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500"></span>Easy</span>
                    <span className="font-bold">{reqEasy}</span>
                  </div>
                  <div className="flex justify-between text-slate-700">
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500"></span>Medium</span>
                    <span className="font-bold">{reqMed}</span>
                  </div>
                  <div className="flex justify-between text-slate-700">
                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500"></span>Hard</span>
                    <span className="font-bold">{reqHard}</span>
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-3 flex justify-between items-center">
                  <span className="font-bold text-slate-900 text-sm">TOTAL QUESTIONS</span>
                  <span className="font-extrabold text-sky-600 text-base">{totalReq}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
