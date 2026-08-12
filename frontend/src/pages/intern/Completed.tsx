import { Link, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export function Completed() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { signOut, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setDropdownOpen(false);
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div className="fixed inset-0 z-[100] bg-background text-on-surface flex flex-col font-body-main overflow-y-auto">
      {/* Header */}
      <header className="bg-surface-container-lowest border-b border-outline-variant h-16 flex items-center px-xl shrink-0 z-40 sticky top-0">
        <div className="flex items-center gap-md w-full max-w-max_content_width mx-auto">
          <img 
            alt="Thozhil Logo" 
            className="w-auto shrink-0" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCLsJ01OJGptmGwzeBqJ9jCAr9RVggtdb6_gt8gsxL3CYDaKu5lLADHzwiKM6BqI3UMaDF9UR0N8PO7EnZrrMvzvW1pB9lqpUiAd3MRK5Ca-wISCXsY-Ec54c8lWwFLo83KCowCXgq4S06rrD3ucusgcrXM9epQ8_CX-ZrKd5S0ShF3kiGRuJ7wHxoRY2vzGLkzb_DG5atjzeBiSLMkOwlErWdzfV7g6JQjBRh3endJgIeNQbAXvAwmu730IsXPbOvThQ" 
            style={{ width: '160px', height: 'auto' }} 
          />
          <div className="ml-auto relative" ref={dropdownRef}>
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)} 
              className="flex items-center gap-md text-on-surface-variant hover:text-primary transition-colors focus:outline-none cursor-pointer"
            >
              <span className="material-symbols-outlined text-[24px]">account_circle</span>
            </button>
            {dropdownOpen && (
              <div className="absolute top-full right-0 mt-2 w-[200px] bg-surface-container-lowest border border-outline-variant rounded shadow-lg py-sm z-50 flex flex-col">
                <div className="px-md pb-sm mb-sm border-b border-outline-variant flex flex-col">
                  <span className="font-navigation text-navigation text-on-surface truncate">{user?.name || 'Intern'}</span>
                  <span className="font-metadata text-metadata text-secondary capitalize">{user?.role || 'Intern'}</span>
                </div>
                <button 
                  onClick={handleLogout}
                  className="flex items-center gap-sm px-md py-xs text-error hover:bg-error-container transition-colors font-navigation text-navigation w-full text-left cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">logout</span>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Canvas */}
      <main className="flex-grow flex items-center justify-center p-xl">
        <div className="w-full max-w-2xl mx-auto bg-surface-container-lowest border border-outline-variant rounded-xl p-xl flex flex-col items-center text-center">
          {/* Central Success Indicator */}
          <div className="w-16 h-16 rounded-full bg-surface-container-low border border-primary-container flex items-center justify-center mb-lg">
            <span className="material-symbols-outlined text-primary-container text-4xl">check</span>
          </div>
          
          {/* Title & Body */}
          <h2 className="font-page-title text-page-title text-on-surface mb-sm">Interview submitted</h2>
          <p className="font-body-main text-body-main text-secondary mb-xl max-w-md mx-auto">
            Your coding interview has been successfully submitted. Your responses have been recorded and are now locked.
          </p>
          
          {/* Interview Summary Box */}
          <div className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-md mb-lg text-left">
            <div className="grid grid-cols-2 gap-y-sm gap-x-md">
              <div className="flex flex-col">
                <span className="font-metadata text-metadata text-secondary mb-1">Interview</span>
                <span className="font-card-title text-card-title text-on-surface">Technical Coding Interview</span>
              </div>
              <div className="flex flex-col">
                <span className="font-metadata text-metadata text-secondary mb-1">Questions</span>
                <span className="font-card-title text-card-title text-on-surface">5</span>
              </div>
              <div className="flex flex-col">
                <span className="font-metadata text-metadata text-secondary mb-1">Status</span>
                <span className="font-card-title text-card-title text-primary-container flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: '"FILL" 1' }}>lock</span> Submitted
                </span>
              </div>
              <div className="flex flex-col">
                <span className="font-metadata text-metadata text-secondary mb-1">Timestamp</span>
                <span className="font-card-title text-card-title text-on-surface">Submitted: 10:45 AM, Aug 08, 2026</span>
              </div>
            </div>
          </div>
          
          {/* Next Steps */}
          <div className="w-full bg-surface text-left border border-outline-variant rounded-lg p-md mb-xl">
            <h3 className="font-card-title text-card-title text-on-surface flex items-center gap-sm mb-sm">
              <span className="material-symbols-outlined text-secondary text-[20px]">info</span>
              What happens next?
            </h3>
            <p className="font-body-main text-body-main text-secondary">
              Your submission will be reviewed by the interview team. You will be contacted by the organization regarding the next steps.
            </p>
          </div>
          
          {/* Final Message & Action */}
          <p className="font-body-main text-body-main text-on-surface mb-lg">Thank you for completing your interview.</p>
          <Link to="/intern/interview/overview" className="font-navigation text-navigation text-primary hover:text-primary-fixed-dim transition-colors flex items-center gap-xs">
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Return to overview
          </Link>
        </div>
      </main>
    </div>
  );
}
