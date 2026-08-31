import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { questionBanksService, QuestionBank as QuestionBankType } from '../../services/questionBanks';

export function QuestionBank() {
  const navigate = useNavigate();
  const [banks, setBanks] = useState<QuestionBankType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchBanks();
  }, []);

  const fetchBanks = async () => {
    try {
      setIsLoading(true);
      const data = await questionBanksService.getQuestionBanks();
      setBanks(data);
    } catch (error) {
      console.error('Failed to fetch question banks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      await questionBanksService.uploadQuestionBank(file);
      await fetchBanks();
    } catch (error: any) {
      console.error('Failed to upload file:', error);
      const status = error.response?.status || 'Unknown';
      const detail = error.response?.data?.detail || error.message || 'Upload failed.';
      alert(`Upload failed (${status}):\n${typeof detail === 'string' ? detail : JSON.stringify(detail)}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDropAreaClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <header className="flex justify-between items-start w-full px-xl pt-xl pb-lg bg-background z-10 sticky top-0">
        <div>
          <h1 className="font-page-title text-page-title text-on-surface font-semibold">Question Bank</h1>
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-lg">
          {/* Left Column: Add Question Bank (Span 4) */}
          <div className="lg:col-span-4 flex flex-col gap-lg">
            <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-md flex flex-col h-full">
              <div className="mb-md">
                <h2 className="font-section-heading text-section-heading text-on-surface mb-xs">Add question bank</h2>
                <p className="font-body-main text-body-main text-secondary">Upload a PDF document containing your coding problems.</p>
              </div>
              <div 
                onClick={handleDropAreaClick}
                className="flex-grow border-2 border-dashed border-outline-variant rounded-DEFAULT p-lg flex flex-col items-center justify-center text-center hover:border-primary hover:bg-surface-container-low transition-colors cursor-pointer group"
              >
                <div className="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center mb-md group-hover:bg-primary-container group-hover:text-on-primary transition-colors">
                  <span className="material-symbols-outlined text-[24px] text-secondary group-hover:text-on-primary">
                    {isUploading ? 'hourglass_empty' : 'upload_file'}
                  </span>
                </div>
                <p className="font-body-main text-body-main text-on-surface mb-xs font-medium">
                  {isUploading ? 'Uploading...' : 'Drop a .pdf file here or select a file from your computer'}
                </p>
                <p className="font-metadata text-metadata text-secondary">Accepted format: PDF (.pdf)</p>
              </div>
              <input 
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,application/pdf" 
                className="hidden" 
                type="file" 
                disabled={isUploading}
              />
            </div>
          </div>
          
          {/* Right Column: Question Banks List (Span 8) */}
          <div className="lg:col-span-8 flex flex-col gap-lg">
            <div className="bg-surface-container-lowest border border-outline-variant rounded-DEFAULT p-md flex flex-col h-full">
              <div className="mb-md flex justify-between items-center">
                <h2 className="font-section-heading text-section-heading text-on-surface">Question banks</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-outline-variant bg-surface-container-low/50">
                      <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Name</th>
                      <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Questions</th>
                      <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium hidden sm:table-cell">Uploaded</th>
                      <th className="py-sm px-md font-navigation text-navigation text-secondary font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="font-body-main text-body-main text-on-surface">
                    {isLoading ? (
                      <tr>
                        <td colSpan={4} className="py-md text-center text-secondary">Loading question banks...</td>
                      </tr>
                    ) : banks.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-md text-center text-secondary">No question banks found. Upload one to get started.</td>
                      </tr>
                    ) : (
                      banks.map((bank) => (
                        <tr 
                          key={bank.id} 
                          onClick={() => navigate(`/authority/question-bank/${bank.id}`)} 
                          className="border-b border-outline-variant hover:bg-surface-container-low transition-colors cursor-pointer group"
                        >
                          <td className="py-sm px-md font-medium text-primary group-hover:underline">
                            {bank.title || bank.filename || 'Question Bank'}
                          </td>
                          <td className="py-sm px-md text-secondary">
                            {bank.question_count ?? bank.questions?.length ?? 0} questions
                          </td>
                          <td className="py-sm px-md text-secondary hidden sm:table-cell">
                            {new Date(bank.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-sm px-md">
                            <div className="flex items-center gap-xs">
                              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                              <span className="text-sm text-emerald-700 font-semibold">
                                Ready
                              </span>
                            </div>
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
      </div>
    </>
  );
}
