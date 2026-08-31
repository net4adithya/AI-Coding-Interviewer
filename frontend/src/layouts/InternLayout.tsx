import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { cn } from '@/utils/cn';
import { useAuth } from '@/contexts/AuthContext';

const navigation = [
  { name: 'Overview', href: '/intern/interview/overview', icon: 'dashboard' },
  { name: 'Interview', href: '/intern/interview/workspace', icon: 'code' },
  { name: 'Profile', href: '#', icon: 'person' },
];

export function InternLayout() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { signOut, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isWorkspaceRoute = location.pathname.includes('/workspace');

  // Full-screen coding workspace — no sidebar or app chrome
  if (isWorkspaceRoute) {
    return <Outlet />;
  }

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
    <div className="flex h-screen font-body-main antialiased bg-background text-on-background overflow-hidden">
      {/* SideNavBar */}
      <nav className="w-sidebar_width h-screen fixed left-0 top-0 bg-white border-r border-outline-variant flex flex-col py-xl z-50 hidden md:flex">
        <div className="px-xl mb-lg">
          <div className="flex items-center justify-center">
            <img 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAbu9JbCc331GXKr5lr7Ytwx6748obRLncNnP6Hp7w2CRZDaYzj7tOOzPLEkMiawmXZCd-P5pgKNLkhorE4eVXQaEQ53eSeinmw_WZFMwign-hQh7ZB7Sd8uMiybllgkc0GX_2ye-S3sfua3DUuFNsMSdUyc4o1UpK30-wmzFsgIFoXWV1lHTlRJnzk4zdJhnnYiiTDJ62pRHAQUrYOsZRwJXRMmTrkOXxOFJaV1RRBdnkHItgeGBaTafrICDO0tZWxow" 
              alt="Thozhil Logo" 
              className="w-auto object-contain" 
              style={{ width: '180px' }} 
            />
          </div>
        </div>
        <div className="flex-1 flex flex-col gap-xs px-md">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-md py-sm px-md rounded-DEFAULT transition-colors font-navigation text-navigation',
                  isActive
                    ? 'bg-surface-container-low text-primary border-l-2 border-primary'
                    : 'text-secondary hover:bg-surface-container'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span 
                    className="material-symbols-outlined text-[20px]" 
                    style={isActive ? { fontVariationSettings: '"FILL" 1' } : {}}
                  >
                    {item.icon}
                  </span>
                  <span>{item.name}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
        
        {/* Profile / Logout Dropdown */}
        <div className="px-md mt-auto pt-lg border-t border-outline-variant relative" ref={dropdownRef}>
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-sm px-sm py-xs w-full text-left rounded hover:bg-surface-container-low transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-container"
          >
            <div className="flex flex-col overflow-hidden w-full">
              <span className="font-navigation text-navigation text-on-surface truncate">{user?.name || 'Intern'}</span>
              <span className="font-metadata text-metadata text-secondary capitalize">{user?.role || 'Intern'}</span>
            </div>
          </button>
          
          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute bottom-full left-md mb-2 w-[200px] bg-surface-container-lowest border border-outline-variant rounded shadow-lg py-sm z-50 flex flex-col">
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
      </nav>

      {/* Main Content Wrapper */}
      <div className="flex-1 md:ml-sidebar_width min-h-screen flex flex-col">
        {/* TopAppBar */}
        <header className="docked full-width top-0 sticky z-40 bg-surface-container-lowest border-b border-outline-variant h-16 px-xl flex justify-between items-center">
          <div>
            <h2 className="font-page-title text-page-title text-on-surface text-xl">Your Coding Interview</h2>
            <p className="font-body-main text-body-main text-secondary hidden md:block">Review the interview details before you begin.</p>
          </div>
          <div className="flex items-center gap-sm">
            <button className="p-2 text-on-surface-variant hover:bg-surface-container rounded-full cursor-pointer transition-opacity active:opacity-70">
              <span className="material-symbols-outlined">help</span>
            </button>
            <button className="p-2 text-on-surface-variant hover:bg-surface-container rounded-full cursor-pointer transition-opacity active:opacity-70 relative">
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border border-surface-container-lowest"></span>
            </button>
          </div>
        </header>

        {/* Main Canvas */}
        <main className="flex-1 p-xl max-w-max_content_width mx-auto w-full flex flex-col gap-lg overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
