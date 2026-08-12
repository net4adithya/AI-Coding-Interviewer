import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { cn } from '@/utils/cn';
import { useAuth } from '@/contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/authority/dashboard', icon: 'dashboard' },
  { name: 'Assessments', href: '/authority/interviews', icon: 'assignment' },
  { name: 'Question Banks', href: '/authority/question-bank', icon: 'database' },
  { name: 'Candidates', href: '/authority/candidates', icon: 'group' },
  { name: 'Submissions', href: '/authority/submissions', icon: 'inventory' },
];

export function AuthorityLayout() {
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
    <div className="flex h-full font-body-main antialiased overflow-hidden bg-background text-on-surface">
      {/* SideNavBar */}
      <nav className="fixed left-0 top-0 h-full w-[230px] bg-white border-r border-outline-variant flex flex-col py-lg px-md z-20 hidden md:flex">
        {/* Brand / Profile */}
        <div className="relative mb-6" ref={dropdownRef}>
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-3 px-xs py-1 rounded hover:bg-surface-container-low transition-colors w-full text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-container"
          >
            <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center shrink-0 overflow-hidden border border-outline-variant">
              <img 
                alt="Thozhil Logo" 
                className="w-full h-full object-cover" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAarGzQI4AtmfcR8ngtFmIOsK7qtW3-J4VOviPTebYritdCnw-kvCmJpZ7pcdkJUMbLYtoT56K7s-AWPFP9OuImA2QHmKw-IzyBY6UwsPeONncv_MOhWF3Hq531E5Fw-0ShYrt2kj9QbMMYXJy6PwRqBjdNW2H1v8hEZRfqQvrwQuNOpH59Wfq82H8zFqVNdr2xygps1xuTJbatfrVeDRIQYUT9enM6FKAyTudmskUNKhAvLj8-fQWprqAzXHMONbUncg" 
              />
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="font-navigation text-on-surface truncate font-medium text-card-title">{user?.name || 'Arun Kumar'}</span>
              <span className="font-metadata text-metadata text-secondary truncate capitalize">{user?.role || 'Authority'}</span>
            </div>
          </button>
          
          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-[200px] bg-surface-container-lowest border border-outline-variant rounded shadow-lg py-sm z-50 flex flex-col">
              <div className="px-md pb-sm mb-sm border-b border-outline-variant flex flex-col">
                <span className="font-navigation text-navigation text-on-surface truncate">{user?.name || 'Arun Kumar'}</span>
                <span className="font-metadata text-metadata text-secondary capitalize">{user?.role || 'Authority'}</span>
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

        {/* Navigation Links */}
        <ul className="flex flex-col gap-1 flex-1">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-sm py-xs rounded font-navigation text-navigation transition-colors group relative',
                    isActive
                      ? 'bg-surface-container-low text-primary-container'
                      : 'text-secondary hover:bg-surface-container-highest'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-primary-container rounded-r"></div>
                    )}
                    <span 
                      className="material-symbols-outlined" 
                      style={isActive ? { fontVariationSettings: '"FILL" 1' } : {}}
                    >
                      {item.icon}
                    </span>
                    <span>{item.name}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="mt-auto flex flex-col gap-1">
          <a className="flex items-center gap-3 px-sm py-xs rounded text-secondary font-navigation text-navigation hover:bg-surface-container-highest transition-colors" href="#">
            <span className="material-symbols-outlined">monitoring</span>
            <span>Analytics</span>
          </a>
          <a className="flex items-center gap-3 px-sm py-xs rounded text-secondary font-navigation text-navigation hover:bg-surface-container-highest transition-colors" href="#">
            <span className="material-symbols-outlined">settings</span>
            <span>Settings</span>
          </a>
        </div>
        <button className="mt-md w-full bg-primary-container text-white py-2 rounded text-sm font-semibold tracking-wide hover:opacity-90 transition-opacity">
          WORKSPACE
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="flex-grow flex flex-col min-h-screen w-full md:pl-[230px]">
        <Outlet />
      </main>
    </div>
  );
}
