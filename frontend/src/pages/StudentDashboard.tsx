import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  Award,
  BookOpen,
  Calendar,
  ChevronRight,
  ExternalLink,
  FileEdit,
  FolderGit2,
  GraduationCap,
  History,
  Plus,
  Sparkles,
  UserCheck,
} from 'lucide-react';
import { recommendationsApi } from '../api/recommendations';
import { studentsApi } from '../api/students';
import { Badge, SyntheticBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useAuth } from '../context/AuthContext';
import { RecommendationHistoryItem, StudentProfile } from '../types';

export const StudentDashboard: React.FC = () => {
  const { user, studentId, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [history, setHistory] = useState<RecommendationHistoryItem[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyStudentId, setHistoryStudentId] = useState<string | null>(null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async (targetId: string) => {
    setIsHistoryLoading(true);
    setHistoryError(null);
    try {
      const histRes = await recommendationsApi.getHistory(targetId);
      const runItems = Array.isArray(histRes?.runs) ? histRes.runs : [];
      setHistory(runItems);
    } catch (err: any) {
      setHistory([]);
      setHistoryError(err.message || 'Recommendation history is unavailable.');
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      // If user has student_id, fetch profile; otherwise fall back to listing students to find match
      let targetId = studentId;
      try {
        if (!targetId && !authLoading) {
          const listRes = await studentsApi.listStudents({ page_size: 1 });
          if (listRes.items.length > 0) {
            targetId = listRes.items[0].id;
          }
        }

        if (targetId) {
          const prof = await studentsApi.getStudent(targetId);
          setProfile(prof);
          setHistoryStudentId(targetId);
          await loadHistory(targetId);
        } else {
          setError('No student profile found for this account.');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load student dashboard.');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [studentId, authLoading, loadHistory]);

  if (isLoading) {
    return <LoadingSpinner message="Loading your student research profile..." size="lg" />;
  }

  if (error || !profile) {
    return (
      <EmptyState
        icon={<AlertCircle className="w-8 h-8 text-rose-400" />}
        title="Student Profile Not Found"
        description={error || 'Please create or link your student profile to access the dashboard.'}
        actionText="Create Student Profile"
        actionIcon={<Plus className="w-4 h-4" />}
        onAction={() => navigate('/student/profile/edit')}
      />
    );
  }

  // Calculate profile completeness score
  let completeness = 20; // Base: Account exists
  if (profile.statement_of_purpose && profile.statement_of_purpose.length > 20) completeness += 25;
  if (profile.bio) completeness += 15;
  if (profile.skills_interests && profile.skills_interests.length > 0) completeness += 20;
  if (profile.academic_projects && profile.academic_projects.length > 0) completeness += 20;

  const isSynthetic =
    profile.statement_of_purpose?.includes('[SYNTHETIC]') ||
    profile.student_number?.startsWith('SYNTH');

  return (
    <div className="space-y-8">
      {/* Header Profile Card */}
      <div className="relative rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-brand-950/40 border border-slate-800 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-brand-500/20 shrink-0">
              {profile.first_name[0]}
              {profile.last_name[0]}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold text-white">
                  {profile.first_name} {profile.last_name}
                </h1>
                {isSynthetic && <SyntheticBadge />}
                <Badge variant="primary" size="sm">
                  {profile.degree_level}
                </Badge>
                <Badge
                  variant={profile.availability_status === 'SEEKING_ADVISOR' ? 'success' : 'neutral'}
                  size="sm"
                >
                  {profile.availability_status.replace(/_/g, ' ')}
                </Badge>
              </div>

              <p className="text-sm text-slate-300">
                Department of {profile.department}
                {profile.graduation_year && ` • Class of ${profile.graduation_year}`}
                {profile.gpa_or_standing && ` • GPA: ${profile.gpa_or_standing.toFixed(2)}`}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<FileEdit className="w-4 h-4" />}
              onClick={() => navigate('/student/profile/edit')}
            >
              Edit Profile
            </Button>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Sparkles className="w-4 h-4 text-brand-300 animate-pulse" />}
              className="glow-brand"
              onClick={() => navigate('/recommendations')}
            >
              Get AI Matches
            </Button>
          </div>
        </div>

        {/* Profile Completeness Bar */}
        <div className="mt-8 pt-6 border-t border-slate-800/80">
          <div className="flex justify-between items-center text-xs mb-2">
            <span className="text-slate-300 font-medium flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-brand-400" />
              Profile Completeness for Vector Embedding
            </span>
            <span className="font-mono text-brand-300 font-bold">{completeness}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-500 to-indigo-400 rounded-full transition-all duration-700"
              style={{ width: `${completeness}%` }}
            />
          </div>
          {completeness < 100 && (
            <p className="text-[11px] text-slate-400 mt-2">
              Tip: Add more academic projects and technical skills to maximize embedding precision in faculty matches.
            </p>
          )}
        </div>
      </div>

      {/* Main Grid: Research Intent & Skills */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Research Statement & Background */}
        <div className="lg:col-span-2 space-y-8">
          {/* Statement of Purpose */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-brand-400" />
                <h2 className="text-lg font-bold text-white">Research Intent & Statement</h2>
              </div>
              <Link
                to="/student/profile/edit"
                className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
              >
                Edit <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              {profile.statement_of_purpose}
            </p>
            {profile.bio && (
              <div className="mt-4">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Academic Background
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">{profile.bio}</p>
              </div>
            )}
          </Card>

          {/* Academic Projects */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-5 h-5 text-indigo-400" />
                <h2 className="text-lg font-bold text-white">
                  Academic & Research Projects ({profile.academic_projects?.length || 0})
                </h2>
              </div>
              <Link
                to="/student/profile/edit"
                className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
              >
                Manage <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {profile.academic_projects && profile.academic_projects.length > 0 ? (
              <div className="space-y-4">
                {profile.academic_projects.map((proj) => (
                  <div
                    key={proj.id}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <h4 className="text-sm font-semibold text-white">{proj.title}</h4>
                      {proj.role && (
                        <Badge variant="neutral" size="sm">
                          {proj.role}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      {proj.description}
                    </p>
                    {proj.github_url && (
                      <a
                        href={proj.github_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 font-mono"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {proj.github_url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 border border-dashed border-slate-800 rounded-xl">
                <FolderGit2 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400 mb-3">No academic projects added yet.</p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => navigate('/student/profile/edit')}
                >
                  Add Your First Project
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Taxonomy Skills & Recommendation History */}
        <div className="space-y-8">
          {/* Skills and Taxonomy */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold text-white">Skills & Interests</h2>
              </div>
              <Link
                to="/student/profile/edit"
                className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
              >
                Edit <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {profile.skills_interests && profile.skills_interests.length > 0 ? (
              <div className="space-y-2.5">
                {profile.skills_interests.map((si) => {
                  const skillName = si.topic_skill?.name || 'Topic Skill';
                  return (
                    <div
                      key={si.id}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
                    >
                      <span className="font-medium text-slate-200">{skillName}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-400 font-mono">
                          Prof: {si.proficiency_level}/5
                        </span>
                        <div className="flex gap-0.5">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <span
                              key={level}
                              className={`w-1.5 h-3 rounded-xs ${
                                level <= si.proficiency_level ? 'bg-emerald-400' : 'bg-slate-800'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6 border border-dashed border-slate-800 rounded-xl">
                <p className="text-xs text-slate-400 mb-3">No skills linked to taxonomy yet.</p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => navigate('/student/profile/edit')}
                >
                  Add Skills
                </Button>
              </div>
            )}
          </Card>

          {/* Past Recommendation Runs */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <History className="w-5 h-5 text-brand-400" />
                <h2 className="text-base font-bold text-white">Recent Match Runs</h2>
              </div>
            </div>

            {historyError ? (
              <div className="text-center py-6">
                <p className="text-xs text-rose-300 mb-3">
                  Recommendation history is unavailable: {historyError}
                </p>
                <Button
                  size="sm"
                  variant="secondary"
                  isLoading={isHistoryLoading}
                  onClick={() => historyStudentId && loadHistory(historyStudentId)}
                  disabled={!historyStudentId}
                >
                  Retry History
                </Button>
              </div>
            ) : history.length > 0 ? (
              <div className="space-y-3">
                {history.slice(0, 4).map((run) => (
                  <div
                    key={run.run_id}
                    onClick={() => navigate('/recommendations')}
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-brand-500/40 cursor-pointer transition-colors"
                  >
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="font-medium text-slate-200 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                        {run.algorithm_version}
                      </span>
                      <span className="font-mono text-[10px] text-slate-500">
                        {typeof run.execution_time_ms === 'number'
                          ? `${run.execution_time_ms.toFixed(1)} ms`
                          : `${run.execution_time_ms} ms`}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {new Date(run.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <Sparkles className="w-7 h-7 text-brand-400/40 mx-auto mb-2" />
                <p className="text-xs text-slate-400 mb-3">No recommendation runs yet.</p>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => navigate('/recommendations')}
                >
                  Generate First Match
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
