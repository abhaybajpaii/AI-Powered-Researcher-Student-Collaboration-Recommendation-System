import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  Award,
  BookOpen,
  Building,
  CheckCircle2,
  ExternalLink,
  Globe,
  MapPin,
  Sparkles,
  Users,
} from 'lucide-react';
import { facultyApi } from '../api/faculty';
import { Badge, SyntheticBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { FacultyProfile } from '../types';

export const FacultyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [faculty, setFaculty] = useState<FacultyProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFaculty = async () => {
      if (!id) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await facultyApi.getFaculty(id);
        setFaculty(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load researcher profile.');
      } finally {
        setIsLoading(false);
      }
    };

    loadFaculty();
  }, [id]);

  if (isLoading) {
    return <LoadingSpinner message="Loading researcher profile and publications..." size="lg" />;
  }

  if (error || !faculty) {
    return (
      <EmptyState
        icon={<AlertCircle className="w-8 h-8 text-rose-400" />}
        title="Researcher Profile Not Found"
        description={error || 'The requested researcher profile does not exist.'}
        actionText="Back to Directory"
        onAction={() => navigate('/directory')}
      />
    );
  }

  const isSynthetic =
    faculty.faculty_number?.startsWith('SYNTH') ||
    faculty.bio?.includes('[SYNTHETIC]');

  const availableSlots = faculty.max_capacity - faculty.current_student_count;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Back button */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>
      </div>

      {/* Profile Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
          <div className="flex items-start gap-5">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-indigo-600 via-brand-600 to-violet-500 flex items-center justify-center text-white text-3xl font-bold shadow-xl shadow-brand-500/20 shrink-0">
              {faculty.first_name[0]}
              {faculty.last_name[0]}
            </div>

            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-bold text-white">
                  {faculty.first_name} {faculty.last_name}
                </h1>
                {isSynthetic && <SyntheticBadge />}
                <Badge variant="primary" size="sm">
                  {faculty.title_rank.replace(/_/g, ' ')}
                </Badge>
              </div>

              <div className="flex items-center gap-2 text-sm text-slate-300">
                <Building className="w-4 h-4 text-slate-400 shrink-0" />
                <span>Department of {faculty.department}</span>
              </div>

              {faculty.lab_name && (
                <div className="text-sm font-semibold text-brand-300">
                  {faculty.lab_name}
                </div>
              )}

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
                {faculty.office_location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    {faculty.office_location}
                  </span>
                )}
                {faculty.website_url && (
                  <a
                    href={faculty.website_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-brand-400 hover:text-brand-300 underline"
                  >
                    <Globe className="w-3.5 h-3.5" />
                    Lab Website
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Mentorship Capacity Box */}
          <div className="sm:text-right p-4 rounded-xl bg-slate-950/80 border border-slate-800 shrink-0 space-y-2">
            <div className="text-xs text-slate-400 font-medium">Advising & Lab Capacity</div>
            <div className="flex items-center gap-2 sm:justify-end">
              <Badge
                variant={faculty.accepting_students ? 'success' : 'neutral'}
                size="md"
              >
                {faculty.accepting_students ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Accepting Students
                  </>
                ) : (
                  'Lab Currently Full'
                )}
              </Badge>
            </div>
            <div className="text-xs text-slate-300 font-mono">
              <span className="font-semibold text-white">{faculty.current_student_count}</span>
              <span className="text-slate-500"> / {faculty.max_capacity} advised</span>
              {availableSlots > 0 && (
                <span className="text-emerald-400 ml-1.5 font-sans">({availableSlots} open)</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Research Biography & Expertise */}
        <div className="lg:col-span-2 space-y-8">
          {/* Research Bio */}
          <Card>
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-brand-400" />
              Research Narrative & Biography
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-800">
              {faculty.bio || 'No biography provided.'}
            </p>
          </Card>

          {/* Publications */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                Verified Publications ({faculty.authorship_links?.length || 0})
              </h2>
            </div>

            {faculty.authorship_links && faculty.authorship_links.length > 0 ? (
              <div className="space-y-4">
                {faculty.authorship_links.map((link) => {
                  const pub = link.publication;
                  if (!pub) return null;

                  return (
                    <div
                      key={pub.id}
                      className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3 mb-1.5">
                        <h4 className="font-semibold text-sm text-white leading-snug">
                          {pub.title}
                        </h4>
                        {pub.publication_year && (
                          <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded shrink-0">
                            {pub.publication_year}
                          </span>
                        )}
                      </div>

                      {pub.venue && (
                        <div className="text-xs text-brand-300/80 font-medium mb-2">
                          {pub.venue}
                        </div>
                      )}

                      {pub.abstract && (
                        <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 mb-3">
                          {pub.abstract}
                        </p>
                      )}

                      <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                        {pub.doi && (
                          <span className="font-mono text-slate-500">
                            DOI: {pub.doi}
                          </span>
                        )}
                        {pub.citation_count !== undefined && (
                          <span>Citations: {pub.citation_count}</span>
                        )}
                        {pub.url && (
                          <a
                            href={pub.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-400 hover:text-brand-300 inline-flex items-center gap-1"
                          >
                            <ExternalLink className="w-3 h-3" /> Paper Link
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-4">No publication records linked yet.</p>
            )}
          </Card>
        </div>

        {/* Right Column: Taxonomy Research Topics */}
        <div className="space-y-8">
          <Card>
            <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <Award className="w-5 h-5 text-emerald-400" />
              Primary Research Expertise
            </h2>

            {faculty.skills_expertise && faculty.skills_expertise.length > 0 ? (
              <div className="space-y-2">
                {faculty.skills_expertise.map((exp) => (
                  <div
                    key={exp.id}
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between"
                  >
                    <span className="font-medium text-slate-200">
                      {exp.topic_skill?.name || 'Topic Skill'}
                    </span>
                    {exp.is_primary_focus ? (
                      <span className="text-[10px] text-brand-300 font-semibold bg-brand-500/20 px-2 py-0.5 rounded border border-brand-500/30">
                        Primary Focus
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400 font-mono">
                        Lvl {exp.expertise_level}/5
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No expertise nodes mapped.</p>
            )}
          </Card>

          {/* Connect Action Box */}
          <Card className="border-brand-500/20 bg-brand-950/10 text-center space-y-3">
            <Sparkles className="w-8 h-8 text-brand-400 mx-auto" />
            <h3 className="font-bold text-white text-base">Check Your Match Compatibility</h3>
            <p className="text-xs text-slate-300">
              Run the recommendation engine to see how your research statement and project portfolio score against this professor's publications.
            </p>
            <Button
              className="w-full mt-2"
              onClick={() => navigate('/recommendations')}
            >
              Run AI Match
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};
