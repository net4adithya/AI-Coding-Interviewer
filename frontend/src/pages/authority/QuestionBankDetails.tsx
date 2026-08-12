import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { questionBanksService, QuestionBank as QuestionBankType, Question } from '../../services/questionBanks';

export function QuestionBankDetails() {
  const { id } = useParams<{ id: string }>();
  const [bank, setBank] = useState<QuestionBankType | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [topicFilter, setTopicFilter] = useState('All');
  const [difficultyFilter, setDifficultyFilter] = useState('All');
  const [languageFilter, setLanguageFilter] = useState('All');

  useEffect(() => {
    if (id) {
      fetchBankDetails(parseInt(id, 10));
    }
  }, [id]);

  const fetchBankDetails = async (bankId: number) => {
    try {
      setIsLoading(true);
      const [bankData, questionsData] = await Promise.all([
        questionBanksService.getQuestionBank(bankId),
        questionBanksService.getQuestions(bankId)
      ]);
      setBank(bankData);
      setQuestions(questionsData);
    } catch (error) {
      console.error('Failed to fetch question bank details:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="p-xl">Loading...</div>;
  }

  if (!bank) {
    return <div className="p-xl">Question bank not found.</div>;
  }

  // Derive summary metrics
  const uniqueTopics = Array.from(new Set(questions.map(q => q.topic)));
  const easyCount = questions.filter(q => q.difficulty === 'EASY').length;
  const medCount = questions.filter(q => q.difficulty === 'MEDIUM').length;
  const hardCount = questions.filter(q => q.difficulty === 'HARD').length;
  const allLangs = Array.from(new Set(questions.flatMap(q => q.programming_languages)));

  // Apply filters
  const filteredQuestions = questions.filter(q => {
    const matchesSearch = q.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTopic = topicFilter === 'All' || q.topic === topicFilter;
    const matchesDiff = difficultyFilter === 'All' || q.difficulty === difficultyFilter.toUpperCase();
    const matchesLang = languageFilter === 'All' || q.programming_languages.includes(languageFilter);
    return matchesSearch && matchesTopic && matchesDiff && matchesLang;
  });

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg bg-background z-10 sticky top-0">
        <div className="flex items-start gap-sm">
          <Link to="/authority/question-bank" className="mt-1 w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors text-secondary hover:text-primary cursor-pointer">
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </Link>
          <div>
            <div className="font-metadata text-metadata text-secondary mb-base">Question Bank / {bank.filename}</div>
            <h1 className="font-page-title text-page-title text-on-surface font-semibold mb-xs">{bank.filename}</h1>
          </div>
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
        <div className="space-y-lg">
          {/* Page Header & Action */}
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-sm mb-xs">
                <h2 className="font-section-heading text-section-heading text-on-surface">Overview</h2>
                <span className={`inline-flex items-center px-2 py-1 rounded bg-surface-container-low text-xs font-medium border ${bank.status === 'COMPLETED' ? 'text-primary border-primary/20' : 'text-secondary border-outline'}`}>
                  {bank.status === 'COMPLETED' ? 'Ready' : bank.status}
                </span>
              </div>
              <p className="font-metadata text-metadata text-secondary">{bank.question_count} questions · Uploaded {new Date(bank.created_at).toLocaleDateString()}</p>
            </div>
            <button className="bg-primary-container text-white px-md py-[8px] rounded font-navigation text-navigation hover:opacity-90 transition-opacity">
              Use for assessment
            </button>
          </div>

          {/* Summary Grid */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-md grid grid-cols-4 gap-md">
            <div className="flex flex-col gap-base border-r border-outline-variant pr-md">
              <span className="font-metadata text-metadata text-secondary uppercase tracking-wider">Total Questions</span>
              <span className="font-section-heading text-section-heading text-on-surface">{questions.length}</span>
            </div>
            <div className="flex flex-col gap-base border-r border-outline-variant pr-md">
              <span className="font-metadata text-metadata text-secondary uppercase tracking-wider">Topics Covered</span>
              <span className="font-body-main text-body-main text-on-surface truncate">
                {uniqueTopics.slice(0, 3).join(', ')}{uniqueTopics.length > 3 ? '...' : ''}
              </span>
            </div>
            <div className="flex flex-col gap-base border-r border-outline-variant pr-md">
              <span className="font-metadata text-metadata text-secondary uppercase tracking-wider">Difficulty Split</span>
              <div className="flex gap-sm font-metadata text-metadata mt-xs">
                <span className="text-emerald-600">{easyCount} Easy</span>
                <span className="text-amber-600">{medCount} Med</span>
                <span className="text-rose-600">{hardCount} Hard</span>
              </div>
            </div>
            <div className="flex flex-col gap-base">
              <span className="font-metadata text-metadata text-secondary uppercase tracking-wider">Supported Languages</span>
              <div className="flex flex-wrap gap-xs mt-xs">
                {allLangs.slice(0, 5).map(lang => (
                  <span key={lang} className="px-2 py-[2px] bg-surface-container text-on-surface-variant text-[11px] rounded">{lang}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Questions Section */}
          <div className="pt-sm">
            <div className="mb-md">
              <h2 className="font-section-heading text-section-heading text-on-surface">Questions</h2>
              <p className="font-metadata text-metadata text-secondary">Questions extracted from this question bank.</p>
            </div>
            
            {/* Filters and Search */}
            <div className="flex justify-between items-center mb-md">
              <div className="flex gap-sm">
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-secondary text-[18px]">search</span>
                  <input 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-xl pr-md py-sm bg-surface-container-lowest border border-outline-variant rounded font-body-main text-body-main w-[240px] focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container placeholder:text-secondary" 
                    placeholder="Search questions" 
                    type="text" 
                  />
                </div>
                <select 
                  value={topicFilter}
                  onChange={(e) => setTopicFilter(e.target.value)}
                  className="px-md py-sm bg-surface-container-lowest border border-outline-variant rounded font-body-main text-body-main text-on-surface appearance-none pr-8 relative cursor-pointer focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                >
                  <option value="All">Topic: All</option>
                  {uniqueTopics.map(topic => (
                    <option key={topic} value={topic}>{topic}</option>
                  ))}
                </select>
                <select 
                  value={difficultyFilter}
                  onChange={(e) => setDifficultyFilter(e.target.value)}
                  className="px-md py-sm bg-surface-container-lowest border border-outline-variant rounded font-body-main text-body-main text-on-surface appearance-none pr-8 relative cursor-pointer focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                >
                  <option value="All">Difficulty: All</option>
                  <option value="EASY">Easy</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HARD">Hard</option>
                </select>
                <select 
                  value={languageFilter}
                  onChange={(e) => setLanguageFilter(e.target.value)}
                  className="px-md py-sm bg-surface-container-lowest border border-outline-variant rounded font-body-main text-body-main text-on-surface appearance-none pr-8 relative cursor-pointer focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                >
                  <option value="All">Language: All</option>
                  {allLangs.map(lang => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </div>
              <span className="font-metadata text-metadata text-secondary">Showing {filteredQuestions.length} of {questions.length} questions</span>
            </div>
            
            {/* Table */}
            <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low/50 border-b border-outline-variant">
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium w-12">#</th>
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Question</th>
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium w-[140px]">Topic</th>
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium w-[100px]">Difficulty</th>
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium w-[100px]">Time</th>
                    <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium w-[180px]">Languages</th>
                  </tr>
                </thead>
                <tbody className="font-body-main text-body-main">
                  {filteredQuestions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-md text-center text-secondary">No questions found matching criteria.</td>
                    </tr>
                  ) : (
                    filteredQuestions.map((q, index) => (
                      <tr key={q.id} className="border-b border-outline-variant hover:bg-surface-container-low transition-colors group cursor-pointer">
                        <td className="py-sm px-md text-secondary">{index + 1}</td>
                        <td className="py-sm px-md font-medium text-primary">{q.title}</td>
                        <td className="py-sm px-md text-secondary">{q.topic}</td>
                        <td className="py-sm px-md">
                          <span className={
                            q.difficulty === 'EASY' ? 'text-emerald-600 font-medium' :
                            q.difficulty === 'MEDIUM' ? 'text-amber-600 font-medium' :
                            'text-rose-600 font-medium'
                          }>
                            {q.difficulty.charAt(0) + q.difficulty.slice(1).toLowerCase()}
                          </span>
                        </td>
                        <td className="py-sm px-md text-secondary">{q.expected_time_minutes ? `${q.expected_time_minutes} min` : '-'}</td>
                        <td className="py-sm px-md text-secondary text-[12px] truncate max-w-[150px]">
                          {q.programming_languages.join(', ')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
