import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FolderGit2,
  Plus,
  Save,
  Sparkles,
  Trash2,
  User,
} from 'lucide-react';
import { studentsApi } from '../api/students';
import { taxonomyApi } from '../api/taxonomy';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import { useAuth } from '../context/AuthContext';
import { StudentProfile, TopicSkill } from '../types';

export const StudentProfileEditor: React.FC = () => {
  const { studentId, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [allTopics, setAllTopics] = useState<TopicSkill[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const isSavingRef = useRef(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals for adding items
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isSkillModalOpen, setIsSkillModalOpen] = useState(false);

  // New project state
  const [newProject, setNewProject] = useState({
    title: '',
    description: '',
    role: '',
    github_url: '',
  });

  // New skill state
  const [newSkill, setNewSkill] = useState({
    topic_skill_id: '',
    proficiency_level: 3,
    interest_level: 5,
    years_experience: 1,
  });

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let targetId = studentId;
      if (!targetId && !authLoading) {
        const listRes = await studentsApi.listStudents({ page_size: 1 });
        if (listRes.items.length > 0) targetId = listRes.items[0].id;
      }

      if (targetId) {
        const prof = await studentsApi.getStudent(targetId);
        setProfile(prof);
      }

      const topics = await taxonomyApi.listTopics();
      setAllTopics(topics);
      if (topics.length > 0 && !newSkill.topic_skill_id) {
        setNewSkill((prev) => ({ ...prev, topic_skill_id: topics[0].id }));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load profile for editing.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    loadData();
  }, [studentId, authLoading]);

  const handleProfileFieldChange = (field: keyof StudentProfile, value: any) => {
    if (!profile) return;
    setProfile({
      ...profile,
      [field]: value,
    });
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || isSavingRef.current) return;
    isSavingRef.current = true;
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const updated = await studentsApi.updateStudent(profile.id, {
        first_name: profile.first_name,
        last_name: profile.last_name,
        department: profile.department,
        degree_level: profile.degree_level,
        gpa_or_standing: profile.gpa_or_standing,
        graduation_year: profile.graduation_year,
        bio: profile.bio,
        statement_of_purpose: profile.statement_of_purpose,
        availability_status: profile.availability_status,
      });
      setProfile((prev) => (prev ? { ...prev, ...updated } : updated));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save changes.');
    } finally {
      isSavingRef.current = false;
      setIsSaving(false);
    }
  };

  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      const added = await studentsApi.addProject(profile.id, newProject);
      setProfile({
        ...profile,
        academic_projects: [...(profile.academic_projects || []), added],
      });
      setIsProjectModalOpen(false);
      setNewProject({ title: '', description: '', role: '', github_url: '' });
    } catch (err: any) {
      setError(err.message || 'Failed to add project.');
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!profile) return;
    try {
      await studentsApi.deleteProject(profile.id, projectId);
      setProfile({
        ...profile,
        academic_projects: profile.academic_projects.filter((p) => p.id !== projectId),
      });
    } catch (err: any) {
      setError(err.message || 'Failed to delete project.');
    }
  };

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      await studentsApi.addSkill(profile.id, newSkill);
      // Re-fetch profile to get fully loaded taxonomy topic, but preserve local uncommitted edits
      const refetched = await studentsApi.getStudent(profile.id);
      setProfile((prev) => (prev ? { ...prev, skills_interests: refetched.skills_interests } : refetched));
      setIsSkillModalOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to add skill.');
    }
  };

  const handleDeleteSkill = async (skillInterestId: string) => {
    if (!profile) return;
    try {
      await studentsApi.deleteSkill(profile.id, skillInterestId);
      setProfile({
        ...profile,
        skills_interests: profile.skills_interests.filter((s) => s.id !== skillInterestId),
      });
    } catch (err: any) {
      setError(err.message || 'Failed to remove skill.');
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading profile editor..." size="lg" />;
  }

  if (!profile) {
    return (
      <div className="text-center py-12">
        <p className="text-rose-400">Profile not loaded.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/student/dashboard')}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">Edit Student Profile</h1>
            <p className="text-xs text-slate-400">
              Update your research statement, skills, and projects to improve AI matching accuracy.
            </p>
          </div>
        </div>

        <Button
          type="submit"
          form="profile-form"
          isLoading={isSaving}
          leftIcon={<Save className="w-4 h-4" />}
        >
          Save All Changes
        </Button>
      </div>

      {saveSuccess && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Profile updated successfully! Embeddings will reflect new text on next match run.</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Form */}
      <form id="profile-form" onSubmit={handleSaveProfile} className="space-y-8">
        {/* Core Demographics */}
        <Card>
          <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <User className="w-4 h-4 text-brand-400" />
            Academic Background
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="profile-first-name" className="block text-xs font-medium text-slate-300 mb-1">First Name</label>
              <input
                id="profile-first-name"
                type="text"
                required
                value={profile.first_name}
                onChange={(e) => handleProfileFieldChange('first_name', e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="profile-last-name" className="block text-xs font-medium text-slate-300 mb-1">Last Name</label>
              <input
                id="profile-last-name"
                type="text"
                required
                value={profile.last_name}
                onChange={(e) => handleProfileFieldChange('last_name', e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div>
              <label htmlFor="profile-department" className="block text-xs font-medium text-slate-300 mb-1">Department</label>
              <input
                id="profile-department"
                type="text"
                required
                value={profile.department}
                onChange={(e) => handleProfileFieldChange('department', e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="profile-degree-level" className="block text-xs font-medium text-slate-300 mb-1">Degree Level</label>
              <select
                id="profile-degree-level"
                value={profile.degree_level}
                onChange={(e) => handleProfileFieldChange('degree_level', e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              >
                <option value="UNDERGRADUATE">Undergraduate</option>
                <option value="MASTERS">Master's</option>
                <option value="PHD">Ph.D.</option>
              </select>
            </div>
            <div>
              <label htmlFor="profile-availability-status" className="block text-xs font-medium text-slate-300 mb-1">
                Availability Status
              </label>
              <select
                id="profile-availability-status"
                value={profile.availability_status}
                onChange={(e) => handleProfileFieldChange('availability_status', e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              >
                <option value="SEEKING_ADVISOR">Seeking Advisor</option>
                <option value="OPEN_TO_PROJECTS">Open to Projects</option>
                <option value="NOT_AVAILABLE">Not Currently Available</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="profile-gpa" className="block text-xs font-medium text-slate-300 mb-1">
                GPA / Standing (optional)
              </label>
              <input
                id="profile-gpa"
                type="number"
                step="0.01"
                min="0.0"
                max="4.0"
                value={profile.gpa_or_standing || ''}
                onChange={(e) =>
                  handleProfileFieldChange(
                    'gpa_or_standing',
                    e.target.value ? parseFloat(e.target.value) : null
                  )
                }
                placeholder="3.85"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="profile-graduation-year" className="block text-xs font-medium text-slate-300 mb-1">
                Expected Graduation Year
              </label>
              <input
                id="profile-graduation-year"
                type="number"
                min="2024"
                max="2032"
                value={profile.graduation_year || ''}
                onChange={(e) =>
                  handleProfileFieldChange(
                    'graduation_year',
                    e.target.value ? parseInt(e.target.value, 10) : null
                  )
                }
                placeholder="2027"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>
        </Card>

        {/* Research Intent Statement */}
        <Card>
          <div className="mb-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span id="profile-statement-label">Statement of Purpose & Research Goals</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              This text is converted into dense semantic vectors to match faculty publications and biographies.
            </p>
          </div>
          <textarea
            id="profile-statement"
            aria-labelledby="profile-statement-label"
            rows={5}
            required
            value={profile.statement_of_purpose}
            onChange={(e) => handleProfileFieldChange('statement_of_purpose', e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:border-brand-500 leading-relaxed font-sans"
          />

          <div className="mt-4">
            <label htmlFor="profile-bio" className="block text-xs font-medium text-slate-300 mb-1">
              Supplementary Academic Bio
            </label>
            <textarea
              id="profile-bio"
              rows={3}
              value={profile.bio || ''}
              onChange={(e) => handleProfileFieldChange('bio', e.target.value)}
              placeholder="Prior degrees, awards, or lab experience..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            />
          </div>
        </Card>

        {/* Academic Projects Section */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-indigo-400" />
                Academic & Capstone Projects
              </h2>
              <p className="text-xs text-slate-400">
                Applied research evidence evaluated against faculty paper abstracts.
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setIsProjectModalOpen(true)}
            >
              Add Project
            </Button>
          </div>

          <div className="space-y-3">
            {profile.academic_projects && profile.academic_projects.length > 0 ? (
              profile.academic_projects.map((proj) => (
                <div
                  key={proj.id}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-white">{proj.title}</span>
                      {proj.role && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {proj.role}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{proj.description}</p>
                    {proj.github_url && (
                      <span className="text-[11px] text-brand-400 font-mono block">
                        {proj.github_url}
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteProject(proj.id)}
                    className="text-slate-500 hover:text-rose-400 p-1.5 transition-colors cursor-pointer"
                    title="Remove project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic py-2">No projects added yet.</p>
            )}
          </div>
        </Card>

        {/* Taxonomy Skills Section */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Taxonomy Skills & Research Topics
              </h2>
              <p className="text-xs text-slate-400">
                Used to compute the Jaccard Skill Compatibility match score.
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setIsSkillModalOpen(true)}
            >
              Add Skill
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {profile.skills_interests && profile.skills_interests.length > 0 ? (
              profile.skills_interests.map((si) => (
                <div
                  key={si.id}
                  className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200"
                >
                  <span className="font-medium">{si.topic_skill?.name || 'Topic Skill'}</span>
                  <span className="text-[10px] text-brand-400 font-mono">Lvl {si.proficiency_level}</span>
                  <button
                    type="button"
                    onClick={() => handleDeleteSkill(si.id)}
                    className="text-slate-500 hover:text-rose-400 p-0.5 cursor-pointer"
                    title="Remove skill"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic py-2">No skills selected yet.</p>
            )}
          </div>
        </Card>

        <div className="flex justify-end pt-4">
          <Button
            type="submit"
            size="lg"
            isLoading={isSaving}
            leftIcon={<Save className="w-5 h-5" />}
          >
            Save All Changes
          </Button>
        </div>
      </form>

      {/* Modal: Add Project */}
      <Modal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        title="Add Academic Project"
      >
        <form onSubmit={handleAddProject} className="space-y-4">
          <div>
            <label htmlFor="project-title" className="block text-xs font-medium text-slate-300 mb-1">Project Title</label>
            <input
              id="project-title"
              type="text"
              required
              value={newProject.title}
              onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
              placeholder="e.g. Transformer-Based Code Summarizer"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label htmlFor="project-role" className="block text-xs font-medium text-slate-300 mb-1">Your Role</label>
            <input
              id="project-role"
              type="text"
              value={newProject.role}
              onChange={(e) => setNewProject({ ...newProject, role: e.target.value })}
              placeholder="e.g. Lead Author / ML Engineer"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label htmlFor="project-description" className="block text-xs font-medium text-slate-300 mb-1">Description</label>
            <textarea
              id="project-description"
              rows={4}
              required
              value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
              placeholder="Describe objectives, methods, datasets, models used, and findings..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label htmlFor="project-url" className="block text-xs font-medium text-slate-300 mb-1">
              Repository or Project URL (optional)
            </label>
            <input
              id="project-url"
              type="url"
              value={newProject.github_url}
              onChange={(e) => setNewProject({ ...newProject, github_url: e.target.value })}
              placeholder="https://github.com/..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsProjectModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Save Project</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Add Skill */}
      <Modal
        isOpen={isSkillModalOpen}
        onClose={() => setIsSkillModalOpen(false)}
        title="Add Taxonomy Skill or Research Topic"
      >
        <form onSubmit={handleAddSkill} className="space-y-4">
          <div>
            <label htmlFor="skill-topic" className="block text-xs font-medium text-slate-300 mb-1">Select Topic / Skill</label>
            <select
              id="skill-topic"
              value={newSkill.topic_skill_id}
              onChange={(e) => setNewSkill({ ...newSkill, topic_skill_id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            >
              {allTopics.map((t) => (
                <option key={t.id} value={t.id}>
                  [{t.category}] {t.name}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="skill-proficiency" className="block text-xs font-medium text-slate-300 mb-1">
                Proficiency Level (1-5)
              </label>
              <input
                id="skill-proficiency"
                type="number"
                min="1"
                max="5"
                value={newSkill.proficiency_level}
                onChange={(e) =>
                  setNewSkill({ ...newSkill, proficiency_level: parseInt(e.target.value, 10) })
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label htmlFor="skill-interest" className="block text-xs font-medium text-slate-300 mb-1">
                Interest Level (1-5)
              </label>
              <input
                id="skill-interest"
                type="number"
                min="1"
                max="5"
                value={newSkill.interest_level}
                onChange={(e) =>
                  setNewSkill({ ...newSkill, interest_level: parseInt(e.target.value, 10) })
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsSkillModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Add to Profile</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
