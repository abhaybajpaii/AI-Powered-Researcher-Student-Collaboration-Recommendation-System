import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  BookOpen,
  Building,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Database,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  Filter,
  Globe,
  Layers,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  UserCheck,
  Users,
  XCircle,
} from 'lucide-react';
import { adminApi } from '../api/admin';
import { embeddingsApi } from '../api/embeddings';
import { evaluationApi } from '../api/evaluation';
import {
  scholarlyApi,
  ScholarlyAuthorPreview,
  ScholarlyDataSummary,
  ScholarlyWorkPreview,
  VerificationFacultyItem,
} from '../api/scholarly';
import {
  Badge,
  RealDataBadge,
  SyntheticBadge,
  VerificationBadge,
} from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import {
  DataCountsResponse,
  EmbeddingStatsResponse,
  EvaluationBenchmarkResponse,
  ImportJob,
} from '../types';

type AdminTab = 'overview' | 'real_ingestion' | 'faculty_verification' | 'jobs';
const VERIFICATION_PAGE_SIZE = 20;

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');

  // Overview states
  const [counts, setCounts] = useState<DataCountsResponse | null>(null);
  const [scholarlySummary, setScholarlySummary] = useState<ScholarlyDataSummary | null>(null);
  const [importJobs, setImportJobs] = useState<ImportJob[]>([]);
  const [embeddingStats, setEmbeddingStats] = useState<EmbeddingStatsResponse | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<EvaluationBenchmarkResponse | null>(null);
  const [loadErrors, setLoadErrors] = useState<
    Partial<Record<'counts' | 'jobs' | 'embeddings' | 'summary', string>>
  >({});

  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isBenchmarking, setIsBenchmarking] = useState(false);

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  // Seed parameters
  const [seedConfig, setSeedConfig] = useState({
    students: 30,
    faculty: 25,
    publications: 60,
    seed: 42,
  });

  // ---------------------------------------------------------------------------
  // Real Research Ingestion States
  // ---------------------------------------------------------------------------
  const [ingestMode, setIngestMode] = useState<'works' | 'authors' | 'csv'>('works');
  const [searchQuery, setSearchQuery] = useState('natural language processing');
  const [institutionRor, setInstitutionRor] = useState('');
  const [fromYear, setFromYear] = useState<number>(2020);
  const [isSearching, setIsSearching] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const [worksResults, setWorksResults] = useState<ScholarlyWorkPreview[]>([]);
  const [authorsResults, setAuthorsResults] = useState<ScholarlyAuthorPreview[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [enrichCrossref, setEnrichCrossref] = useState(true);

  // CSV Roster Upload State
  const [csvContent, setCsvContent] = useState('');
  const [csvImportResult, setCsvImportResult] = useState<any | null>(null);

  // ---------------------------------------------------------------------------
  // Faculty Verification Review States
  // ---------------------------------------------------------------------------
  const [verificationItems, setVerificationItems] = useState<VerificationFacultyItem[]>([]);
  const [verificationFilter, setVerificationFilter] = useState<string>('ALL');
  const [verificationPage, setVerificationPage] = useState(1);
  const [verificationTotal, setVerificationTotal] = useState(0);
  const [isVerificationLoading, setIsVerificationLoading] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [editingFaculty, setEditingFaculty] = useState<VerificationFacultyItem | null>(null);
  const [editForm, setEditForm] = useState({
    status: 'VERIFIED',
    notes: '',
    department: '',
    title_rank: '',
  });

  const loadAllAdminData = async () => {
    setIsLoading(true);
    const [countsResult, jobsResult, embeddingsResult, summaryResult] =
      await Promise.allSettled([
        adminApi.getDataCounts(),
        scholarlyApi.getJobs(),
        embeddingsApi.getStats(),
        scholarlyApi.getSummary(),
      ]);
    const nextErrors: typeof loadErrors = {};
    const getMessage = (reason: unknown) =>
      reason instanceof Error ? reason.message : String(reason);

    if (countsResult.status === 'fulfilled') setCounts(countsResult.value);
    else nextErrors.counts = getMessage(countsResult.reason);

    if (jobsResult.status === 'fulfilled') setImportJobs(jobsResult.value);
    else nextErrors.jobs = getMessage(jobsResult.reason);

    if (embeddingsResult.status === 'fulfilled') setEmbeddingStats(embeddingsResult.value);
    else nextErrors.embeddings = getMessage(embeddingsResult.reason);

    if (summaryResult.status === 'fulfilled') setScholarlySummary(summaryResult.value);
    else nextErrors.summary = getMessage(summaryResult.reason);

    setLoadErrors(nextErrors);
    setIsLoading(false);
  };

  useEffect(() => {
    loadAllAdminData();
  }, []);

  const loadVerificationFaculty = async (statusFilter: string, page: number) => {
    setIsVerificationLoading(true);
    setVerificationError(null);
    try {
      const filter = statusFilter !== 'ALL' ? statusFilter : undefined;
      const res = await scholarlyApi.listVerificationFaculty({
        status_filter: filter,
        page,
        per_page: VERIFICATION_PAGE_SIZE,
      });
      setVerificationItems(res.items);
      setVerificationTotal(res.total);
    } catch (err: any) {
      setVerificationItems([]);
      setVerificationTotal(0);
      setVerificationError(err.message || 'Failed to load faculty verification records.');
    } finally {
      setIsVerificationLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'faculty_verification') {
      loadVerificationFaculty(verificationFilter, verificationPage);
    }
  }, [activeTab, verificationFilter, verificationPage]);

  // ---------------------------------------------------------------------------
  // Synthetic Data Handlers
  // ---------------------------------------------------------------------------
  const handleSeedSynthetic = async () => {
    setIsSeeding(true);
    setNotification(null);
    try {
      const res = await adminApi.seedSynthetic({
        num_students: seedConfig.students,
        num_faculty: seedConfig.faculty,
        num_publications: seedConfig.publications,
        seed: seedConfig.seed,
      });
      setNotification({
        type: 'success',
        text: `Synthetic dataset successfully seeded! Import Job ID: ${res.job_id}`,
      });
      await loadAllAdminData();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Seeding failed.' });
    } finally {
      setIsSeeding(false);
    }
  };

  const handleResetSynthetic = async () => {
    if (!window.confirm('Are you sure you want to delete all synthetic data? Real imported research data will be safely preserved.')) {
      return;
    }
    setIsResetting(true);
    setNotification(null);
    try {
      const res = await adminApi.resetSynthetic();
      setNotification({
        type: 'success',
        text: `Synthetic data safely purged. Real scholarly records preserved.`,
      });
      await loadAllAdminData();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Reset failed.' });
    } finally {
      setIsResetting(false);
    }
  };

  const handleSyncEmbeddings = async () => {
    setIsEmbedding(true);
    setNotification(null);
    try {
      const res = await embeddingsApi.syncAll();
      setNotification({
        type: 'success',
        text: `Vector embeddings synchronized across all entities! (${res.dimension}-dim ${res.model_name})`,
      });
      await loadAllAdminData();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Embedding sync failed.' });
    } finally {
      setIsEmbedding(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsBenchmarking(true);
    setNotification(null);
    try {
      const res = await evaluationApi.runBenchmark('standard_eval_v1', '5,10');
      setBenchmarkResult(res);
      setNotification({
        type: 'success',
        text: `Offline benchmark executed! Evaluated across relevance judgments.`,
      });
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Benchmark evaluation failed.' });
    } finally {
      setIsBenchmarking(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Real Ingestion Handlers
  // ---------------------------------------------------------------------------
  const handleOpenAlexSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setSelectedIds(new Set());
    setNotification(null);

    try {
      if (ingestMode === 'works') {
        const res = await scholarlyApi.searchWorks(
          searchQuery,
          institutionRor || undefined,
          fromYear || undefined,
          1,
          12
        );
        setWorksResults(res.results);
      } else if (ingestMode === 'authors') {
        const res = await scholarlyApi.searchAuthors(
          searchQuery,
          institutionRor || undefined,
          1,
          12
        );
        setAuthorsResults(res.results);
      }
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Scholarly search failed.' });
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSelectId = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    if (ingestMode === 'works') {
      if (selectedIds.size === worksResults.length) setSelectedIds(new Set());
      else setSelectedIds(new Set(worksResults.map((w) => w.openalex_id)));
    } else {
      if (selectedIds.size === authorsResults.length) setSelectedIds(new Set());
      else setSelectedIds(new Set(authorsResults.map((a) => a.openalex_id)));
    }
  };

  const handleImportSelected = async () => {
    if (selectedIds.size === 0) return;
    setIsImporting(true);
    setNotification(null);

    try {
      if (ingestMode === 'works') {
        const selectedWorks = worksResults.filter((w) => selectedIds.has(w.openalex_id));
        const res = await scholarlyApi.importWorks(selectedWorks, enrichCrossref, true);
        setNotification({
          type: 'success',
          text: `Successfully imported ${res.created} publications (${res.updated} updated). Embeddings generated.`,
        });
      } else if (ingestMode === 'authors') {
        const selectedAuthors = authorsResults.filter((a) => selectedIds.has(a.openalex_id));
        const res = await scholarlyApi.importAuthors(
          selectedAuthors,
          'Computer Science',
          'PENDING_REVIEW',
          true
        );
        setNotification({
          type: 'success',
          text: `Successfully imported ${res.created} researchers as pending faculty profiles.`,
        });
      }
      setSelectedIds(new Set());
      await loadAllAdminData();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Import failed.' });
    } finally {
      setIsImporting(false);
    }
  };

  const handleImportCsvRoster = async () => {
    if (!csvContent.trim()) return;
    setIsImporting(true);
    setNotification(null);
    try {
      const res = await scholarlyApi.importCsv(csvContent, true);
      setCsvImportResult(res);
      setNotification({
        type: 'success',
        text: `Institutional CSV imported! Created: ${res.created}, Updated: ${res.updated}. Status: VERIFIED.`,
      });
      await loadAllAdminData();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'CSV roster import failed.' });
    } finally {
      setIsImporting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Faculty Verification Actions
  // ---------------------------------------------------------------------------
  const handleQuickVerify = async (facultyId: string, newStatus: string) => {
    try {
      await scholarlyApi.updateVerification(facultyId, {
        verification_status: newStatus,
        verification_notes: `Status updated to ${newStatus} by administrator on ${new Date().toLocaleDateString()}.`,
      });
      await loadVerificationFaculty(verificationFilter, verificationPage);
      await loadAllAdminData();
      setNotification({
        type: 'success',
        text: `Faculty verification status changed to '${newStatus}'.`,
      });
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Verification update failed.' });
    }
  };

  const handleSaveFacultyEdit = async () => {
    if (!editingFaculty) return;
    try {
      await scholarlyApi.updateVerification(editingFaculty.id, {
        verification_status: editForm.status,
        verification_notes: editForm.notes,
        department: editForm.department,
        title_rank: editForm.title_rank,
      });
      setEditingFaculty(null);
      await loadVerificationFaculty(verificationFilter, verificationPage);
      await loadAllAdminData();
      setNotification({
        type: 'success',
        text: 'Faculty verification details updated successfully.',
      });
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to update faculty details.' });
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await scholarlyApi.retryJob(jobId);
      await loadAllAdminData();
      setNotification({ type: 'success', text: 'Import job retry started.' });
    } catch (err: any) {
      setNotification({
        type: 'error',
        text: err.message || 'Import job retry is unavailable.',
      });
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Title & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Platform Governance & Scholarly Data Hub</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Admin Console</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage genuine OpenAlex research ingestion, faculty verification review, synthetic benchmarks, and vector embeddings.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={loadAllAdminData}
          leftIcon={<RefreshCw className="w-4 h-4" />}
        >
          Refresh Live Metrics
        </Button>
      </div>

      {notification && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center gap-3 animate-fade-in ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 shrink-0" />
          )}
          <span className="leading-relaxed">{notification.text}</span>
        </div>
      )}

      {Object.entries(loadErrors).map(([section, message]) => (
        <div
          key={section}
          role="alert"
          className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs"
        >
          Could not load {section === 'embeddings' ? 'embedding statistics' : section === 'summary' ? 'scholarly summary' : section === 'jobs' ? 'import jobs' : 'data counts'}: {message}
        </div>
      ))}

      {/* Top Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Student Profiles</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-purple-300">
            {loadErrors.counts
              ? 'Unavailable'
              : counts?.by_entity?.students?.total?.toLocaleString() ?? (isLoading ? 'Loading…' : '—')}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {counts ? `${counts.summary.total_records.toLocaleString()} Total DB Records` : 'Active student profiles'}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Real Faculty (OpenAlex/CSV)</span>
            <Globe className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-300">
            {loadErrors.summary
              ? 'Unavailable'
              : scholarlySummary?.faculty?.real_count ?? (isLoading ? 'Loading…' : '—')}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {loadErrors.summary
              ? 'Verification totals unavailable'
              : scholarlySummary
                ? `${scholarlySummary.faculty.by_verification_status.VERIFIED ?? 0} Verified • ${scholarlySummary.faculty.by_verification_status.PENDING_REVIEW ?? 0} Pending`
                : 'Verification totals unavailable'}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Synthetic Mode Records</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-300">
            {loadErrors.summary
              ? 'Unavailable'
              : scholarlySummary
                ? `${scholarlySummary.faculty.synthetic_count} Fac • ${scholarlySummary.publications.synthetic_count} Pubs`
                : '—'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Isolated test ecosystem</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Stored Vector Embeddings</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-indigo-300">
            {loadErrors.embeddings
              ? 'Unavailable'
              : isLoading
                ? 'Loading…'
                : embeddingStats?.total_embeddings ?? '—'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">384-dimensional cosine indexed</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Import Jobs Audit</span>
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-300">
            {loadErrors.jobs ? 'Unavailable' : isLoading ? 'Loading…' : importJobs.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Provenance audit logs</div>
        </Card>
      </div>

      {/* Main Tab Navigation */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
            activeTab === 'overview'
              ? 'bg-slate-800 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Overview & Synthetic Engine
        </button>

        <button
          onClick={() => setActiveTab('real_ingestion')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
            activeTab === 'real_ingestion'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Globe className="w-4 h-4 text-cyan-400" />
          Real Research Ingestion (OpenAlex & Crossref)
        </button>

        <button
          onClick={() => setActiveTab('faculty_verification')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
            activeTab === 'faculty_verification'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <UserCheck className="w-4 h-4 text-emerald-400" />
          Faculty Verification Review
        </button>

        <button
          onClick={() => setActiveTab('jobs')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
            activeTab === 'jobs'
              ? 'bg-slate-800 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Import Jobs Audit Log
        </button>
      </div>

      {/* =====================================================================
          TAB 1: Overview & Synthetic Reseeding
         ===================================================================== */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Action Card: Synthetic Generator */}
          <Card>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <h2 className="text-base font-bold text-white">Synthetic Dataset Generator</h2>
              </div>
              <SyntheticBadge />
            </div>

            <p className="text-xs text-slate-300 leading-relaxed mb-6">
              Generates an isolated, reproducible academic ecosystem for testing matching algorithms and offline IR metrics without touching real research records.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div>
                <label htmlFor="seed-students" className="block text-xs font-medium text-slate-400 mb-1">Students</label>
                <input
                  id="seed-students"
                  type="number"
                  min="5"
                  max="200"
                  value={seedConfig.students}
                  onChange={(e) => setSeedConfig({ ...seedConfig, students: parseInt(e.target.value) || 30 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label htmlFor="seed-faculty" className="block text-xs font-medium text-slate-400 mb-1">Faculty</label>
                <input
                  id="seed-faculty"
                  type="number"
                  min="5"
                  max="100"
                  value={seedConfig.faculty}
                  onChange={(e) => setSeedConfig({ ...seedConfig, faculty: parseInt(e.target.value) || 25 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label htmlFor="seed-publications" className="block text-xs font-medium text-slate-400 mb-1">Publications</label>
                <input
                  id="seed-publications"
                  type="number"
                  min="10"
                  max="300"
                  value={seedConfig.publications}
                  onChange={(e) => setSeedConfig({ ...seedConfig, publications: parseInt(e.target.value) || 60 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label htmlFor="seed-random" className="block text-xs font-medium text-slate-400 mb-1">Random Seed</label>
                <input
                  id="seed-random"
                  type="number"
                  value={seedConfig.seed}
                  onChange={(e) => setSeedConfig({ ...seedConfig, seed: parseInt(e.target.value) || 42 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button
                variant="primary"
                onClick={handleSeedSynthetic}
                isLoading={isSeeding}
                leftIcon={<Play className="w-4 h-4" />}
              >
                Seed Synthetic Ecosystem
              </Button>

              <Button
                variant="danger"
                onClick={handleResetSynthetic}
                isLoading={isResetting}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                Purge Synthetic Data Only
              </Button>
            </div>
          </Card>

          {/* Action Card: Embedding & Benchmark */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800 mb-4">
                <Cpu className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-bold text-white">Vector Embedding Synchronization</h2>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                Generates normalized 384-dimensional dense sentence transformer vectors (<code className="font-mono text-brand-300">all-MiniLM-L6-v2</code>) across student profiles, project statements, faculty bios, and publication abstracts.
              </p>
              <Button
                variant="secondary"
                onClick={handleSyncEmbeddings}
                isLoading={isEmbedding}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Synchronize All Embeddings
              </Button>
            </Card>

            <Card>
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800 mb-4">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold text-white">Offline IR Benchmark Evaluator</h2>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                Computes Precision@K, Recall@K, NDCG@K, and Mean Reciprocal Rank against relevance judgments, comparing hybrid embedding ranking against the TF-IDF lexical baseline.
              </p>
              <Button
                variant="primary"
                onClick={handleRunBenchmark}
                isLoading={isBenchmarking}
                leftIcon={<Play className="w-4 h-4" />}
              >
                Run Benchmark Evaluation
              </Button>
            </Card>
          </div>

          {/* Benchmark Results Display */}
          {benchmarkResult && (
            <Card className="animate-fade-in border-emerald-500/30">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-bold text-white">Live Benchmark Evaluation Metrics</h3>
                <Badge variant="success">Offline Eval v1</Badge>
              </div>

              {benchmarkResult.message && (
                <p role="status" className="mb-4 text-sm text-slate-300">
                  {benchmarkResult.message}
                </p>
              )}
              {benchmarkResult.hybrid_embedding_scores ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-center mb-6">
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">NDCG@5</div>
                    <div className="text-2xl font-bold text-emerald-400">
                      {benchmarkResult.hybrid_embedding_scores['ndcg@5'] ?? '—'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Precision@5</div>
                    <div className="text-2xl font-bold text-cyan-400">
                      {benchmarkResult.hybrid_embedding_scores['precision@5'] ?? '—'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Recall@5</div>
                    <div className="text-2xl font-bold text-brand-400">
                      {benchmarkResult.hybrid_embedding_scores['recall@5'] ?? '—'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">MRR</div>
                    <div className="text-2xl font-bold text-indigo-400">
                      {benchmarkResult.hybrid_embedding_scores.mrr ?? '—'}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  Benchmark scores are unavailable for this result.
                </p>
              )}
            </Card>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 2: Real Research Ingestion (OpenAlex & Crossref)
         ===================================================================== */}
      {activeTab === 'real_ingestion' && (
        <div className="space-y-6">
          <Card>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 mb-6">
              <div>
                <div className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-base font-bold text-white">Genuine Scholarly Metadata Ingestion</h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Query the official OpenAlex and Crossref APIs to import authentic publications and researchers into PostgreSQL.
                </p>
              </div>

              {/* Sub-mode selector */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                <button
                  onClick={() => setIngestMode('works')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-colors ${
                    ingestMode === 'works' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  Search Works
                </button>
                <button
                  onClick={() => setIngestMode('authors')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-colors ${
                    ingestMode === 'authors' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Users className="w-3.5 h-3.5" />
                  Search Researchers
                </button>
                <button
                  onClick={() => setIngestMode('csv')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-colors ${
                    ingestMode === 'csv' ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Institutional CSV Roster
                </button>
              </div>
            </div>

            {/* Ingestion Search Form */}
            {ingestMode !== 'csv' ? (
              <div className="space-y-4 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label htmlFor="scholarly-search" className="block text-xs font-medium text-slate-400 mb-1">
                      {ingestMode === 'works' ? 'Research Topic / Paper Title' : 'Researcher / Author Name'}
                    </label>
                    <div className="relative">
                      <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                      <input
                        id="scholarly-search"
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleOpenAlexSearch()}
                        placeholder={ingestMode === 'works' ? 'e.g. self-attention graph neural networks' : 'e.g. Yoshua Bengio'}
                        className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="institution-ror" className="block text-xs font-medium text-slate-400 mb-1">
                      Institution ROR Filter (Optional)
                    </label>
                    <input
                      id="institution-ror"
                      type="text"
                      value={institutionRor}
                      onChange={(e) => setInstitutionRor(e.target.value)}
                      placeholder="e.g. https://ror.org/03vek6s52"
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white placeholder-slate-600 font-mono text-xs focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                  <div className="flex items-center gap-4">
                    {ingestMode === 'works' && (
                      <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={enrichCrossref}
                          onChange={(e) => setEnrichCrossref(e.target.checked)}
                          className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500"
                        />
                        <span>Enrich metadata via Crossref (DOI lookup)</span>
                      </label>
                    )}
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleOpenAlexSearch}
                    isLoading={isSearching}
                    leftIcon={<Search className="w-4 h-4" />}
                  >
                    Query OpenAlex API
                  </Button>
                </div>
              </div>
            ) : (
              /* CSV Roster Section */
              <div className="space-y-4 mb-6">
                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300">
                  <div className="flex items-center gap-2 font-semibold text-emerald-400 mb-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Official University Faculty Roster Format</span>
                  </div>
                  <p className="text-slate-400 mb-2">
                    Paste CSV content with required headers: <code>first_name,last_name,email,department,title_rank,max_capacity</code>.
                    Imported profiles are automatically assigned <strong className="text-emerald-400 font-mono">VERIFIED</strong> status.
                  </p>
                  <textarea
                    aria-label="Institutional faculty roster CSV"
                    rows={6}
                    value={csvContent}
                    onChange={(e) => setCsvContent(e.target.value)}
                    placeholder={`first_name,last_name,email,department,title_rank,max_capacity\nAlice,Vanderbilt,a.vanderbilt@university.edu,Computer Science,FULL_PROFESSOR,8\nBob,Sterling,b.sterling@university.edu,Electrical Engineering,ASSOCIATE_PROFESSOR,5`}
                    className="w-full p-3 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <Button
                  variant="primary"
                  onClick={handleImportCsvRoster}
                  isLoading={isImporting}
                  leftIcon={<Upload className="w-4 h-4" />}
                >
                  Import Verified Faculty Roster
                </Button>
              </div>
            )}

            {/* Ingestion Search Results */}
            {ingestMode === 'works' && worksResults.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">
                      Returned <strong className="text-white">{worksResults.length}</strong> genuine publications:
                    </span>
                    <button
                      onClick={toggleSelectAll}
                      className="text-xs text-cyan-400 hover:underline cursor-pointer"
                    >
                      {selectedIds.size === worksResults.length ? 'Deselect All' : 'Select All'}
                    </button>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleImportSelected}
                    isLoading={isImporting}
                    disabled={selectedIds.size === 0}
                    leftIcon={<Upload className="w-4 h-4" />}
                  >
                    Import Selected ({selectedIds.size})
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {worksResults.map((work) => {
                    const isSelected = selectedIds.has(work.openalex_id);
                    return (
                      <div
                        key={work.openalex_id}
                        onClick={() => toggleSelectId(work.openalex_id)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer select-none ${
                          isSelected
                            ? 'bg-cyan-500/10 border-cyan-500/40 shadow-md shadow-cyan-500/10'
                            : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            aria-label={`Select publication ${work.title}`}
                            checked={isSelected}
                            onChange={() => toggleSelectId(work.openalex_id)}
                            className="mt-1 rounded border-slate-700 text-cyan-600 focus:ring-cyan-500"
                          />
                          <div className="flex-1 space-y-2">
                            <h4 className="text-sm font-semibold text-white leading-snug">
                              {work.title}
                            </h4>
                            <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                              {work.venue && <span className="text-slate-300 font-medium">{work.venue}</span>}
                              {work.publication_year && <span>• {work.publication_year}</span>}
                              <span>• {work.citation_count.toLocaleString()} citations</span>
                            </div>

                            <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                              {work.abstract}
                            </p>

                            {work.authors.length > 0 && (
                              <div className="text-[11px] text-slate-500 truncate">
                                Authors: {work.authors.map((a) => a.name).join(', ')}
                              </div>
                            )}

                            <div className="flex items-center gap-2 pt-1 font-mono text-[10px] text-cyan-400">
                              <span>OpenAlex: {work.openalex_id.split('/').pop()}</span>
                              {work.doi && <span>• DOI: {work.doi}</span>}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {ingestMode === 'authors' && authorsResults.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">
                      Returned <strong className="text-white">{authorsResults.length}</strong> scholar profiles:
                    </span>
                    <button
                      onClick={toggleSelectAll}
                      className="text-xs text-cyan-400 hover:underline cursor-pointer"
                    >
                      {selectedIds.size === authorsResults.length ? 'Deselect All' : 'Select All'}
                    </button>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleImportSelected}
                    isLoading={isImporting}
                    disabled={selectedIds.size === 0}
                    leftIcon={<Upload className="w-4 h-4" />}
                  >
                    Import Selected ({selectedIds.size})
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {authorsResults.map((author) => {
                    const isSelected = selectedIds.has(author.openalex_id);
                    return (
                      <div
                        key={author.openalex_id}
                        onClick={() => toggleSelectId(author.openalex_id)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer select-none ${
                          isSelected
                            ? 'bg-cyan-500/10 border-cyan-500/40 shadow-md shadow-cyan-500/10'
                            : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            aria-label={`Select researcher ${author.display_name}`}
                            checked={isSelected}
                            onChange={() => toggleSelectId(author.openalex_id)}
                            className="mt-1 rounded border-slate-700 text-cyan-600 focus:ring-cyan-500"
                          />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="text-sm font-semibold text-white">
                                {author.display_name}
                              </h4>
                              <Badge variant="warning" size="sm">Will Import as Pending Review</Badge>
                            </div>

                            <div className="text-xs text-slate-300">
                              {author.institution_name || 'Independent / Unknown Institution'}
                            </div>

                            <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                              <span>Works: {author.works_count}</span>
                              <span>•</span>
                              <span>Citations: {author.cited_by_count.toLocaleString()}</span>
                            </div>

                            {author.topics && author.topics.length > 0 && (
                              <div className="flex flex-wrap gap-1 pt-1">
                                {author.topics.slice(0, 4).map((t, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400"
                                  >
                                    {t}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* =====================================================================
          TAB 3: Faculty Verification Review
         ===================================================================== */}
      {activeTab === 'faculty_verification' && (
        <div className="space-y-6">
          <Card>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 mb-6">
              <div>
                <div className="flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-emerald-400" />
                  <h2 className="text-base font-bold text-white">Faculty Verification Review</h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Scholarly author records from OpenAlex require administrative review before being marked as verified university faculty.
                </p>
              </div>

              {/* Status filter pills */}
              <div className="flex flex-wrap items-center gap-1.5">
                {['ALL', 'PENDING_REVIEW', 'UNVERIFIED', 'VERIFIED', 'REJECTED_OUTDATED'].map((st) => (
                  <button
                    key={st}
                    onClick={() => {
                      setVerificationFilter(st);
                      setVerificationPage(1);
                    }}
                    aria-pressed={verificationFilter === st}
                    className={`px-3 py-1 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
                      verificationFilter === st
                        ? 'bg-slate-800 text-white border border-slate-700'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {st.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>

            {isVerificationLoading ? (
              <LoadingSpinner message="Loading faculty verification queue..." />
            ) : verificationError ? (
              <div role="alert" className="text-sm text-rose-300">
                Faculty verification records are unavailable: {verificationError}
              </div>
            ) : verificationItems.length === 0 ? (
              <EmptyState
                icon={<UserCheck className="w-8 h-8 text-slate-500" />}
                title="No Faculty in This Queue"
                description={`No faculty profiles matching verification status '${verificationFilter}' found.`}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="py-2.5 px-3">Faculty / Scholar</th>
                      <th className="py-2.5 px-3">Department</th>
                      <th className="py-2.5 px-3">Data Origin</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Notes</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {verificationItems.map((f) => (
                      <tr key={f.id} className="hover:bg-slate-900/40">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-white">
                            {f.first_name} {f.last_name}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {f.institution_name || 'Department Faculty'}
                          </div>
                          {f.openalex_id && (
                            <a
                              href={f.openalex_id}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-cyan-400 hover:underline mt-0.5"
                            >
                              <span>OpenAlex</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </td>
                        <td className="py-3 px-3 text-slate-300 font-medium">
                          {f.department}
                        </td>
                        <td className="py-3 px-3">
                          {f.is_synthetic ? (
                            <SyntheticBadge />
                          ) : (
                            <RealDataBadge source={f.openalex_id ? 'OpenAlex' : 'CSV'} />
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <VerificationBadge status={f.verification_status} />
                        </td>
                        <td className="py-3 px-3 text-slate-400 max-w-xs truncate">
                          {f.verification_notes || '—'}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {f.verification_status !== 'VERIFIED' && (
                              <button
                                onClick={() => handleQuickVerify(f.id, 'VERIFIED')}
                                className="px-2.5 py-1 rounded bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25 border border-emerald-500/30 text-[11px] font-medium cursor-pointer"
                              >
                                Verify
                              </button>
                            )}
                            {f.verification_status !== 'REJECTED_OUTDATED' && (
                              <button
                                onClick={() => handleQuickVerify(f.id, 'REJECTED_OUTDATED')}
                                className="px-2.5 py-1 rounded bg-rose-500/15 text-rose-300 hover:bg-rose-500/25 border border-rose-500/30 text-[11px] font-medium cursor-pointer"
                              >
                                Reject
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setEditingFaculty(f);
                                setEditForm({
                                  status: f.verification_status,
                                  notes: f.verification_notes || '',
                                  department: f.department,
                                  title_rank: f.title_rank,
                                });
                              }}
                              className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:text-white text-[11px] font-medium cursor-pointer"
                            >
                              Edit
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {verificationTotal > 0 && !isVerificationLoading && !verificationError && (
              <div
                aria-label="Faculty verification pagination"
                className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4"
              >
                <span role="status" className="text-xs text-slate-400">
                  Page {verificationPage} of {Math.ceil(verificationTotal / VERIFICATION_PAGE_SIZE)} · {verificationTotal} faculty
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    aria-label="Previous faculty verification page"
                    disabled={verificationPage <= 1}
                    onClick={() => setVerificationPage((page) => page - 1)}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    aria-label="Next faculty verification page"
                    disabled={verificationPage >= Math.ceil(verificationTotal / VERIFICATION_PAGE_SIZE)}
                    onClick={() => setVerificationPage((page) => page + 1)}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </Card>

          {/* Edit Faculty Verification Modal */}
          {editingFaculty && (
            <Modal
              isOpen={true}
              onClose={() => setEditingFaculty(null)}
              title={`Edit Verification: Dr. ${editingFaculty.first_name} ${editingFaculty.last_name}`}
            >
              <div className="space-y-4">
                <div>
                  <label htmlFor="verification-status" className="block text-xs font-medium text-slate-400 mb-1">
                    Verification Status
                  </label>
                  <select
                    id="verification-status"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white"
                  >
                    <option value="VERIFIED">VERIFIED (Confirmed Faculty)</option>
                    <option value="PENDING_REVIEW">PENDING_REVIEW (Under Review)</option>
                    <option value="UNVERIFIED">UNVERIFIED (Imported Scholar)</option>
                    <option value="REJECTED_OUTDATED">REJECTED_OUTDATED (Not Faculty)</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="verification-department" className="block text-xs font-medium text-slate-400 mb-1">
                    Department
                  </label>
                  <input
                    id="verification-department"
                    type="text"
                    value={editForm.department}
                    onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white"
                  />
                </div>

                <div>
                  <label htmlFor="verification-title-rank" className="block text-xs font-medium text-slate-400 mb-1">
                    Title Rank
                  </label>
                  <input
                    id="verification-title-rank"
                    type="text"
                    value={editForm.title_rank}
                    onChange={(e) => setEditForm({ ...editForm, title_rank: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white"
                  />
                </div>

                <div>
                  <label htmlFor="verification-notes" className="block text-xs font-medium text-slate-400 mb-1">
                    Verification Notes & Decision Rationale
                  </label>
                  <textarea
                    id="verification-notes"
                    rows={3}
                    value={editForm.notes}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                    placeholder="e.g. Appointment verified via faculty directory and institutional email domain."
                    className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                  <Button variant="secondary" size="sm" onClick={() => setEditingFaculty(null)}>
                    Cancel
                  </Button>
                  <Button variant="primary" size="sm" onClick={handleSaveFacultyEdit}>
                    Save Decision
                  </Button>
                </div>
              </div>
            </Modal>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 4: Import Jobs Audit Log
         ===================================================================== */}
      {activeTab === 'jobs' && (
        <Card>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-400" />
              <h3 className="text-base font-bold text-white">Ingestion & Import Jobs Audit Log</h3>
            </div>
            <span className="text-xs font-mono text-slate-500">
              {loadErrors.jobs ? 'Unavailable' : `${importJobs.length} recorded`}
            </span>
          </div>

          {loadErrors.jobs ? (
            <p role="alert" className="text-sm text-rose-300 py-4">
              Import job records are unavailable: {loadErrors.jobs}
            </p>
          ) : importJobs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Job ID</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Processed</th>
                    <th className="py-2.5 px-3 text-right">Created</th>
                    <th className="py-2.5 px-3 text-right">Updated</th>
                    <th className="py-2.5 px-3">Errors</th>
                    <th className="py-2.5 px-3 text-right">Timestamp</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {importJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-mono text-slate-300 text-[11px]">
                        {job.id.substring(0, 8)}...
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge
                          variant={job.status.includes('COMPLETED') ? 'success' : job.status === 'RUNNING' ? 'primary' : 'danger'}
                          size="sm"
                        >
                          {job.status}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                        {job.records_processed}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                        +{job.records_created}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-cyan-400">
                        {job.records_updated}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-rose-400 text-[11px]">
                        {job.error_log && job.error_log.length > 0 ? `${job.error_log.length} errors` : 'None'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400 font-mono text-[11px]">
                        {job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        {job.status === 'FAILED' || (job.error_log && job.error_log.length > 0) ? (
                          <button
                            onClick={() => handleRetryJob(job.id)}
                            className="text-xs text-brand-400 hover:underline cursor-pointer"
                          >
                            Retry
                          </button>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic py-4">No import jobs recorded yet.</p>
          )}
        </Card>
      )}
    </div>
  );
};
