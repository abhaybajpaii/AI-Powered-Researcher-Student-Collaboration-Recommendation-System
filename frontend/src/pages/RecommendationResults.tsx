import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  Award,
  BookOpen,
  Building,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  ExternalLink,
  Layers,
  RotateCcw,
  Sliders,
  Sparkles,
  Star,
  Users,
} from 'lucide-react';
import { recommendationsApi } from '../api/recommendations';
import { studentsApi } from '../api/students';
import { Badge, RealDataBadge, SyntheticBadge, VerificationBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import { ScoreBar } from '../components/common/ScoreBar';
import { useAuth } from '../context/AuthContext';
import { RecommendationItem, RecommendationResponse } from '../types';

export const RecommendationResults: React.FC = () => {
  const { studentId } = useAuth();
  const navigate = useNavigate();

  const [currentStudentId, setCurrentStudentId] = useState<string | null>(studentId);
  const [results, setResults] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Operating Mode filter (Real Research vs Synthetic Demo)
  const [dataMode, setDataMode] = useState<'ALL' | 'REAL_ONLY' | 'SYNTHETIC_ONLY'>('ALL');

  // Weight customization
  const [showWeightsConfig, setShowWeightsConfig] = useState(false);
  const [weights, setWeights] = useState({
    research_interest: 0.35,
    project_research: 0.25,
    publication_relevance: 0.25,
    skill_compatibility: 0.15,
  });

  // Filter
  const [onlyAccepting, setOnlyAccepting] = useState(false);

  // Evidence modal state
  const [selectedCandidate, setSelectedCandidate] = useState<RecommendationItem | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState<Record<string, number>>({});

  const executeRecommendationRun = async (
    sId: string,
    selectedDataMode = dataMode
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await recommendationsApi.generate({
        student_id: sId,
        top_k: 10,
        weights: {
          research_interest: weights.research_interest,
          project_research: weights.project_research,
          publication_relevance: weights.publication_relevance,
          skill_compatibility: weights.skill_compatibility,
        },
        filters: {
          only_accepting_students: onlyAccepting ? true : undefined,
          data_mode: selectedDataMode,
        },
      });
      setResults(response);
    } catch (err: any) {
      setError(err.message || 'Failed to generate recommendations.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const initialize = async () => {
      let targetId = currentStudentId;
      if (!targetId) {
        try {
          const listRes = await studentsApi.listStudents({ page_size: 1 });
          if (listRes.items.length > 0) {
            targetId = listRes.items[0].id;
            setCurrentStudentId(targetId);
          }
        } catch {
          // Handled below
        }
      }

      if (targetId) {
        executeRecommendationRun(targetId);
      } else {
        setError('No active student profile available to match. Please sign in as a student.');
      }
    };

    initialize();
  }, []);

  const handleApplyWeights = () => {
    if (currentStudentId) {
      executeRecommendationRun(currentStudentId);
    }
  };

  const handleResetWeights = () => {
    setWeights({
      research_interest: 0.35,
      project_research: 0.25,
      publication_relevance: 0.25,
      skill_compatibility: 0.15,
    });
  };

  const handleFeedback = async (facultyId: string, rating: number) => {
    if (!results) return;
    try {
      // Find candidate
      const cand = results.recommendations.find((c) => c.faculty_id === facultyId);
      if (cand) {
        await recommendationsApi.submitFeedback(results.run_id, cand.faculty_id, rating);
        setFeedbackSuccess((prev) => ({ ...prev, [facultyId]: rating }));
      }
    } catch (err) {
      console.warn('Feedback submit error:', err);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium mb-2">
            <Sparkles className="w-3.5 h-3.5 text-brand-400 animate-pulse" />
            <span>AI Hybrid Recommendation Engine</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Ranked Faculty Collaborator Matches
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Faculty ranked by dense semantic text embeddings, publication abstracts, project synergy, and taxonomy skill compatibility.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowWeightsConfig(!showWeightsConfig)}
            leftIcon={<Sliders className="w-4 h-4" />}
            rightIcon={showWeightsConfig ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          >
            Adjust Algorithm Weights
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => currentStudentId && executeRecommendationRun(currentStudentId)}
            isLoading={isLoading}
            leftIcon={<RotateCcw className="w-4 h-4" />}
          >
            Re-run Match
          </Button>
        </div>
      </div>

      {/* Weight Customization Panel */}
      {showWeightsConfig && (
        <Card className="border-brand-500/30 bg-slate-900/90 animate-slide-up">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-brand-400" />
              Multi-Signal Scoring Weights & Filters
            </h3>
            <button
              onClick={handleResetWeights}
              className="text-xs text-slate-400 hover:text-brand-300 underline cursor-pointer"
            >
              Reset to Defaults
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Research Intent (SOP)</span>
                <span className="font-mono text-brand-400 font-bold">
                  {(weights.research_interest * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.research_interest}
                onChange={(e) =>
                  setWeights({ ...weights, research_interest: parseFloat(e.target.value) })
                }
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Applied Projects</span>
                <span className="font-mono text-indigo-400 font-bold">
                  {(weights.project_research * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.project_research}
                onChange={(e) =>
                  setWeights({ ...weights, project_research: parseFloat(e.target.value) })
                }
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Publication Abstracts</span>
                <span className="font-mono text-cyan-400 font-bold">
                  {(weights.publication_relevance * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.publication_relevance}
                onChange={(e) =>
                  setWeights({ ...weights, publication_relevance: parseFloat(e.target.value) })
                }
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Skill Taxonomy</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {(weights.skill_compatibility * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.skill_compatibility}
                onChange={(e) =>
                  setWeights({ ...weights, skill_compatibility: parseFloat(e.target.value) })
                }
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-slate-800">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyAccepting}
                onChange={(e) => setOnlyAccepting(e.target.checked)}
                className="rounded border-slate-700 text-brand-600 focus:ring-brand-500"
              />
              <span>Filter: Only recommend faculty currently accepting students</span>
            </label>

            <Button size="sm" onClick={handleApplyWeights}>
              Apply & Re-Score
            </Button>
          </div>
        </Card>
      )}

      {/* Execution Diagnostics Bar */}
      {results && (
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
          <div className="flex items-center gap-3">
            <span>
              Evaluated Candidates: <strong className="text-white">{results.total_candidates_evaluated}</strong>
            </span>
            <span>•</span>
            <span>
              Engine Version: <strong className="font-mono text-brand-300">{results.algorithm_version}</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span>Execution Latency:</span>
            <span className="text-emerald-400 font-semibold">{results.execution_time_ms.toFixed(1)} ms</span>
          </div>
        </div>
      )}

      {/* Operating Mode Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="flex items-center gap-2 text-xs">
          <span className="font-semibold text-slate-200">Data Operating Mode:</span>
          <span className="text-slate-400 hidden sm:inline">
            Isolate genuine scholarly records from fictional demo data.
          </span>
        </div>
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => {
              setDataMode('ALL');
              if (currentStudentId) executeRecommendationRun(currentStudentId, 'ALL');
            }}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              dataMode === 'ALL'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Data
          </button>
          <button
            type="button"
            onClick={() => {
              setDataMode('REAL_ONLY');
              if (currentStudentId) executeRecommendationRun(currentStudentId, 'REAL_ONLY');
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              dataMode === 'REAL_ONLY'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            Real Research Only
          </button>
          <button
            type="button"
            onClick={() => {
              setDataMode('SYNTHETIC_ONLY');
              if (currentStudentId) executeRecommendationRun(currentStudentId, 'SYNTHETIC_ONLY');
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              dataMode === 'SYNTHETIC_ONLY'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Synthetic Demo Only
          </button>
        </div>
      </div>

      {/* Recommendation Results List */}
      {isLoading ? (
        <LoadingSpinner message="Computing multi-signal vector embeddings and reranking..." size="lg" />
      ) : error ? (
        <EmptyState
          icon={<AlertCircle className="w-8 h-8 text-rose-400" />}
          title="Recommendation Engine Error"
          description={error}
          actionText="Edit Profile & Retry"
          onAction={() => navigate('/student/profile/edit')}
        />
      ) : !results || results.recommendations.length === 0 ? (
        <EmptyState
          icon={<Users className="w-8 h-8 text-slate-500" />}
          title="No Faculty Matches Available"
          description="Try disabling capacity filters, expanding your statement of purpose, or switching the Data Operating Mode filter."
          actionText="Edit Student Profile"
          onAction={() => navigate('/student/profile/edit')}
        />
      ) : (
        <div className="space-y-6">
          {results.recommendations.map((item) => {
            const matchPercent = Math.round((item.overall_score ?? item.total_score) * 100);
            const userRating = feedbackSuccess[item.faculty_id];

            return (
              <Card
                key={item.faculty_id}
                hoverEffect
                className="border-slate-800/90 hover:border-brand-500/40"
              >
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                  {/* Left: Rank, Name, Explanation */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-start gap-4">
                      {/* Rank Badge */}
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white font-extrabold text-base shadow-md shadow-brand-500/20 shrink-0">
                        #{item.rank_position ?? item.rank}
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3
                            onClick={() => navigate(`/faculty/${item.faculty_id}`)}
                            className="font-bold text-lg text-white hover:text-brand-300 transition-colors cursor-pointer"
                          >
                            {item.faculty_name}
                          </h3>
                          <Badge variant="primary" size="sm">
                            {item.title_rank.replace(/_/g, ' ')}
                          </Badge>
                          {item.is_synthetic === false ? (
                            <div className="flex items-center gap-1.5">
                              <RealDataBadge source={item.openalex_id ? 'OpenAlex' : 'Institutional'} />
                              <VerificationBadge status={item.verification_status} />
                            </div>
                          ) : (
                            <SyntheticBadge />
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <Building className="w-3.5 h-3.5 text-slate-500" />
                          <span>{item.department}</span>
                          {item.lab_name && (
                            <>
                              <span>•</span>
                              <span className="text-brand-300 font-medium">{item.lab_name}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Grounded Explanation Summary */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
                      <p className="text-xs text-slate-200 leading-relaxed">
                        {item.explanation_summary}
                      </p>
                    </div>

                    {/* Shared Skills Tags */}
                    {item.shared_skills && item.shared_skills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] text-slate-400 font-medium mr-1">
                          Compatible Skills:
                        </span>
                        {item.shared_skills.map((skill) => (
                          <span
                            key={skill}
                            className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Caveats */}
                    {((item.missing_data_caveats && item.missing_data_caveats.length > 0) ||
                      (item.caveats && item.caveats.length > 0)) && (
                      <div className="space-y-1 pt-1">
                        {(item.missing_data_caveats || item.caveats || []).map((c, i) => (
                          <div
                            key={i}
                            className="text-[11px] text-amber-300 flex items-center gap-1.5"
                          >
                            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                            <span>{c}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Right: Scores & Action Buttons */}
                  <div className="lg:w-80 shrink-0 p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-4">
                    {/* Overall Score Header */}
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                      <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        Overall Compatibility
                      </span>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold font-mono text-brand-300">
                          {matchPercent}%
                        </span>
                      </div>
                    </div>

                    {/* 4 Score Bars */}
                    <div className="space-y-2.5">
                      <ScoreBar
                        label="Research Intent"
                        score={item.score_breakdown.research_interest_score}
                        weight={
                          item.score_breakdown.normalized_weights?.research_interest ??
                          item.score_breakdown.weights?.research_interest ??
                          0.35
                        }
                      />
                      <ScoreBar
                        label="Project Experience"
                        score={item.score_breakdown.project_research_score}
                        weight={
                          item.score_breakdown.normalized_weights?.project_research ??
                          item.score_breakdown.weights?.project_research ??
                          0.25
                        }
                      />
                      <ScoreBar
                        label="Publication Match"
                        score={item.score_breakdown.publication_relevance_score}
                        weight={
                          item.score_breakdown.normalized_weights?.publication_relevance ??
                          item.score_breakdown.weights?.publication_relevance ??
                          0.25
                        }
                      />
                      <ScoreBar
                        label="Skill Compatibility"
                        score={item.score_breakdown.skill_compatibility_score}
                        weight={
                          item.score_breakdown.normalized_weights?.skill_compatibility ??
                          item.score_breakdown.weights?.skill_compatibility ??
                          0.15
                        }
                      />
                    </div>

                    {/* Action buttons */}
                    <div className="pt-2 flex flex-col gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => setSelectedCandidate(item)}
                        leftIcon={<BookOpen className="w-3.5 h-3.5 text-brand-400" />}
                      >
                        Inspect Evidence ({(item.top_publications || item.relevant_publications || []).length} papers)
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => navigate(`/faculty/${item.faculty_id}`)}
                      >
                        View Full Faculty Profile
                      </Button>
                    </div>

                    {/* User Rating / Feedback */}
                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                      <span>Rate recommendation:</span>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            onClick={() => handleFeedback(item.faculty_id, star)}
                            className="p-1 hover:text-amber-400 transition-colors cursor-pointer"
                            title={`Rate ${star} stars`}
                          >
                            <Star
                              className={`w-3.5 h-3.5 ${
                                userRating && userRating >= star
                                  ? 'text-amber-400 fill-amber-400'
                                  : 'text-slate-600'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Evidence Inspection Modal */}
      <Modal
        isOpen={!!selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
        title={
          selectedCandidate
            ? `Evidence Breakdown: ${selectedCandidate.faculty_name}`
            : 'Evidence'
        }
        maxWidth="2xl"
      >
        {selectedCandidate && (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Algorithm Explanation
              </h4>
              <p className="text-sm text-slate-200 leading-relaxed">
                {selectedCandidate.explanation_summary}
              </p>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-400" />
                Top Relevant Faculty Publications for Your Statement
              </h4>

              {(() => {
                const pubs =
                  selectedCandidate.top_publications ||
                  selectedCandidate.relevant_publications ||
                  [];
                return pubs.length > 0 ? (
                  <div className="space-y-3">
                    {pubs.map((pub) => {
                      const simPercent = Math.round(pub.similarity_score * 100);
                      const pubYear = pub.year ?? pub.publication_year;
                      return (
                        <div
                          key={pub.publication_id}
                          className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-4"
                        >
                          <div className="space-y-1">
                            <h5 className="font-semibold text-xs text-white leading-snug">
                              {pub.title}
                            </h5>
                            {(pub.venue || pubYear) && (
                              <div className="text-[11px] text-brand-300 font-mono">
                                {pub.venue ? pub.venue : ''}
                                {pub.venue && pubYear ? ' ' : ''}
                                {pubYear ? `(${pubYear})` : ''}
                              </div>
                            )}
                            {pub.relevant_excerpt && (
                              <p className="text-[11px] text-slate-400 italic line-clamp-2 mt-1">
                                "{pub.relevant_excerpt}"
                              </p>
                            )}
                          </div>

                          <div className="text-right shrink-0">
                            <span className="font-mono text-xs font-bold text-emerald-400">
                              {simPercent}% match
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No direct publication matches mapped.</p>
                );
              })()}
            </div>

            <div className="flex justify-end pt-2">
              <Button onClick={() => setSelectedCandidate(null)}>Close Inspection</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
