import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { signIn } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error } = await signIn(email, password);
      if (error) {
        setError(error);
      } else {
        // Redirection should actually happen automatically via ProtectedRoute or here based on role.
        // Let's redirect here to be safe, but AuthContext updates state.
        if (email.includes('admin') || email.includes('authority')) {
          navigate('/authority/dashboard');
        } else {
          navigate('/intern/interview/overview');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-surface text-on-surface font-body-main min-h-screen flex flex-col items-center justify-center p-md sm:p-xl w-full">
      <main className="w-full max-w-[420px] bg-surface-container-lowest border border-outline-variant rounded-lg p-xl flex flex-col gap-lg shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        {/* Header */}
        <div className="flex flex-col items-center text-center gap-md">
          <img alt="Thozhil Logo" className="h-16 w-auto object-contain mb-xs mx-auto" src="https://lh3.googleusercontent.com/aida-public/AB6AXuChEwcWssza6SE-5KuG2_D7UXkjIu_RGCMUx6FV-2yAwoD1iqoNHSnAHDafhXOPeVKIKFg3r6_2ltpFj6h_C5ugnbgPSBWKm0WJldv_n-y-Pquq7xFoJqSru6epcCESy_lOhg-WpcfQeAuFO1Ww9-8HX1gVtWY4x5EhQbxmoK-MA4dIrhyndJQ1FQHgshf8pfb0rI_Pyz9nCpREfi1G4xhi4XDqQJwpPKqPOmFvQY9JLI_7w5jqurKOIR7chXNryOD0GQ" />
          <h1 className="font-page-title text-page-title text-on-surface m-0">Welcome back</h1>
          <p className="font-body-main text-body-main text-secondary m-0">Sign in to continue to your assessment workspace.</p>
        </div>
        
        {/* Form */}
        <form className="flex flex-col gap-md" onSubmit={handleLogin}>
          {error && <div className="text-error text-sm text-center">{error}</div>}
          <div className="flex flex-col gap-xs">
            <label className="font-navigation text-navigation text-on-surface" htmlFor="email">Email</label>
            <input 
              className="w-full px-md py-sm bg-surface-container-lowest border border-outline-variant rounded focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors font-body-main text-body-main placeholder:text-secondary-fixed-dim" 
              id="email" 
              placeholder="Enter your email" 
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-xs">
            <div className="flex justify-between items-center">
              <label className="font-navigation text-navigation text-on-surface" htmlFor="password">Password</label>
              <a className="font-metadata text-metadata text-primary-container hover:text-primary transition-colors" href="#">Forgot password?</a>
            </div>
            <div className="relative w-full">
              <input 
                className="w-full px-md py-sm bg-surface-container-lowest border border-outline-variant rounded focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors font-body-main text-body-main placeholder:text-secondary-fixed-dim pr-[40px]" 
                id="password" 
                placeholder="Enter your password" 
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button 
                aria-label="Toggle password visibility" 
                className="absolute right-sm top-1/2 -translate-y-1/2 text-secondary hover:text-on-surface transition-colors flex items-center justify-center p-1" 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
              >
                <span className="material-symbols-outlined text-[20px]">{showPassword ? "visibility_off" : "visibility"}</span>
              </button>
            </div>
          </div>
          <button 
            className="w-full bg-primary-container text-on-primary font-navigation text-navigation rounded px-md py-[10px] mt-xs hover:bg-primary transition-colors cursor-pointer border border-transparent disabled:opacity-50" 
            type="submit"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        
        {/* Divider */}
        <div className="flex items-center gap-sm w-full my-xs">
          <div className="h-px bg-outline-variant flex-1"></div>
          <span className="font-metadata text-metadata text-secondary uppercase tracking-wider">or</span>
          <div className="h-px bg-outline-variant flex-1"></div>
        </div>
        
        {/* Secondary Action */}
        <button className="w-full bg-transparent border border-outline-variant text-on-secondary-fixed font-navigation text-navigation rounded px-md py-[10px] hover:bg-surface-container-low hover:border-outline transition-colors cursor-pointer flex justify-center items-center gap-sm" type="button">
          Continue with organisation
        </button>
      </main>
      
      {/* Footer */}
      <footer className="mt-xl font-metadata text-metadata text-secondary text-center">
        © 2026 Thozhil
      </footer>
    </div>
  );
}
