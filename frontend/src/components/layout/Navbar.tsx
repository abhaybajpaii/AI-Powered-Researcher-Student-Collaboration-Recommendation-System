import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Compass,
  FileEdit,
  GraduationCap,
  Layers,
  LogOut,
  Menu,
  ShieldCheck,
  Sparkles,
  User as UserIcon,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

export const Navbar: React.FC = () => {
  const { user, logout, isStudent, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-brand-500/25 group-hover:scale-105 transition-transform">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                Collab<span className="text-brand-400">Match</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                  AI
                </span>
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden lg:flex items-center gap-1">
            <Link
              to="/directory"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/directory')
                  ? 'bg-slate-800 text-brand-300'
                  : 'text-slate-300 hover:text-white hover:bg-slate-900'
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Compass className="w-4 h-4" />
                Researchers
              </span>
            </Link>

            {isStudent && (
              <>
                <Link
                  to="/student/dashboard"
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive('/student/dashboard')
                      ? 'bg-slate-800 text-brand-300'
                      : 'text-slate-300 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-4 h-4" />
                    Dashboard
                  </span>
                </Link>

                <Link
                  to="/recommendations"
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive('/recommendations')
                      ? 'bg-brand-600/20 text-brand-300 border border-brand-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <span className="flex items-center gap-1.5 text-brand-300 font-semibold">
                    <Sparkles className="w-4 h-4 text-brand-400 animate-pulse" />
                    AI Matches
                  </span>
                </Link>

                <Link
                  to="/student/profile/edit"
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive('/student/profile/edit')
                      ? 'bg-slate-800 text-brand-300'
                      : 'text-slate-300 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <FileEdit className="w-4 h-4" />
                    Edit Profile
                  </span>
                </Link>
              </>
            )}

            {isAdmin && (
              <Link
                to="/admin"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/admin')
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-900'
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  Admin Console
                </span>
              </Link>
            )}
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden lg:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
                  <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200 font-semibold text-xs">
                    {user.first_name ? user.first_name[0] : user.email[0].toUpperCase()}
                  </div>
                  <div className="text-left">
                    <div className="text-xs font-medium text-slate-200 truncate max-w-[120px]">
                      {user.full_name || user.email}
                    </div>
                    <Badge variant={user.role === 'ADMIN' ? 'warning' : 'primary'} size="sm">
                      {user.role}
                    </Badge>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  leftIcon={<LogOut className="w-4 h-4 text-slate-400" />}
                  title="Sign out"
                >
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/login')}
                  leftIcon={<UserIcon className="w-4 h-4" />}
                >
                  Sign In
                </Button>
              </div>
            )}
          </div>

          {/* Mobile menu trigger */}
          <div className="flex lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              aria-label="Toggle mobile menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-slate-800 bg-slate-950 px-4 pt-2 pb-6 space-y-3 animate-fade-in">
          <Link
            to="/directory"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-300 hover:bg-slate-900"
          >
            Researchers Directory
          </Link>
          {isStudent && (
            <>
              <Link
                to="/student/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-300 hover:bg-slate-900"
              >
                Dashboard
              </Link>
              <Link
                to="/recommendations"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-brand-300 hover:bg-slate-900"
              >
                AI Recommendations
              </Link>
              <Link
                to="/student/profile/edit"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-300 hover:bg-slate-900"
              >
                Edit Profile
              </Link>
            </>
          )}
          {isAdmin && (
            <Link
              to="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg text-base font-medium text-indigo-300 hover:bg-slate-900"
            >
              Admin Console
            </Link>
          )}

          <div className="pt-4 border-t border-slate-800 flex flex-col gap-2">
            {user ? (
              <Button
                variant="danger"
                size="md"
                onClick={() => {
                  logout();
                  setMobileMenuOpen(false);
                }}
                leftIcon={<LogOut className="w-4 h-4" />}
                className="w-full"
              >
                Sign Out ({user.email})
              </Button>
            ) : (
              <>
                <Button
                  variant="primary"
                  onClick={() => {
                    navigate('/login');
                    setMobileMenuOpen(false);
                  }}
                  className="w-full"
                >
                  Sign In
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
