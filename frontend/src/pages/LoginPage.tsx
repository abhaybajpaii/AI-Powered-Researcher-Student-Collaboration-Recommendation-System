import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, GraduationCap, Lock, Mail } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const user = await login(email, password);
      const defaultDestination =
        user.role === 'ADMIN'
          ? '/admin'
          : user.role === 'FACULTY'
            ? '/directory'
            : '/student/dashboard';

      let destination = defaultDestination;
      if (from && from !== '/login') {
        const isAdminRoute = from === '/admin' || from.startsWith('/admin/');
        const isStudentRoute = from.startsWith('/student/') || from === '/recommendations';

        if (isAdminRoute && user.role !== 'ADMIN') {
          destination = defaultDestination;
        } else if (isStudentRoute && user.role !== 'STUDENT' && user.role !== 'ADMIN') {
          destination = defaultDestination;
        } else {
          destination = from;
        }
      }
      navigate(destination, { replace: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '';
      setError(message || 'Login failed. Please check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4">
      <div className="text-center mb-8">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-violet-500 mx-auto flex items-center justify-center text-white mb-4 shadow-lg shadow-brand-500/25">
          <GraduationCap className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold text-white">Sign In to CollabMatch</h1>
        <p className="text-sm text-slate-400 mt-1">
          Access your research dashboard and personalized AI matches
        </p>
      </div>

      <Card>
        <p className="mb-5 text-xs text-slate-400">
          Demo accounts are not automatically provisioned. Sign in with an account provided by your administrator.
        </p>
        {error && (
          <div role="alert" aria-live="polite" className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="login-email" className="block text-xs font-medium text-slate-300 mb-1.5">
              University Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@university.edu"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label htmlFor="login-password" className="block text-xs font-medium text-slate-300 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                id="login-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
              />
            </div>
          </div>

          <Button
            type="submit"
            isLoading={isLoading}
            className="w-full mt-2"
            size="md"
          >
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400">
          Don't have an account yet?{' '}
          <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium underline">
            Register here
          </Link>
        </div>
      </Card>
    </div>
  );
};
