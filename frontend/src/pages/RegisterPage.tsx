import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, GraduationCap, Lock, Mail, User } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { useAuth } from '../context/AuthContext';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    role: 'STUDENT' as 'STUDENT' | 'FACULTY',
    first_name: '',
    last_name: '',
    department: 'Computer Science',
    statement_of_purpose: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.role === 'FACULTY') {
      setError(
        'Faculty accounts must be created through the supported faculty onboarding process. Self-registration is currently available for students only.'
      );
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      await register({
        email: formData.email,
        password: formData.password,
        role: formData.role,
        first_name: formData.first_name,
        last_name: formData.last_name,
        department: formData.department,
        statement_of_purpose: formData.statement_of_purpose || 'Passionate about interdisciplinary research.',
      });
      navigate('/student/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please verify details.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10 px-4">
      <div className="text-center mb-8">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 mx-auto flex items-center justify-center text-white mb-4 shadow-lg shadow-brand-500/25">
          <GraduationCap className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold text-white">Create Your Academic Profile</h1>
        <p className="text-sm text-slate-400 mt-1">
          Join the AI-powered researcher–student collaboration platform
        </p>
      </div>

      <Card>
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="register-first-name" className="block text-xs font-medium text-slate-300 mb-1.5">First Name</label>
              <input
                id="register-first-name"
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="Ada"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="register-last-name" className="block text-xs font-medium text-slate-300 mb-1.5">Last Name</label>
              <input
                id="register-last-name"
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="Lovelace"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="register-email" className="block text-xs font-medium text-slate-300 mb-1.5">University Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                id="register-email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="alovelace@university.edu"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="register-role" className="block text-xs font-medium text-slate-300 mb-1.5">Role</label>
              <select
                id="register-role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as 'STUDENT' | 'FACULTY' })}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              >
                <option value="STUDENT">Student</option>
                <option value="FACULTY">Faculty Researcher</option>
              </select>
            </div>
            <div>
              <label htmlFor="register-department" className="block text-xs font-medium text-slate-300 mb-1.5">Department</label>
              <input
                id="register-department"
                type="text"
                required
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                placeholder="Computer Science"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="register-statement" className="block text-xs font-medium text-slate-300 mb-1.5">
              Statement of Research Purpose
            </label>
            <textarea
              id="register-statement"
              rows={3}
              value={formData.statement_of_purpose}
              onChange={(e) => setFormData({ ...formData, statement_of_purpose: e.target.value })}
              placeholder="Describe your research interests, thesis goals, or the problems you wish to investigate..."
              className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="register-password" className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <input
                id="register-password"
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="At least 6 characters"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="register-confirm-password" className="block text-xs font-medium text-slate-300 mb-1.5">Confirm Password</label>
              <input
                id="register-confirm-password"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                placeholder="Repeat password"
                className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <Button
            type="submit"
            isLoading={isLoading}
            className="w-full mt-3"
            size="md"
          >
            Create Account & Profile
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400">
          Already registered?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium underline">
            Sign in
          </Link>
        </div>
      </Card>
    </div>
  );
};
