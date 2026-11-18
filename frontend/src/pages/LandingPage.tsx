import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  BookOpen,
  CheckCircle2,
  Compass,
  Cpu,
  GraduationCap,
  Layers,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { useAuth } from '../context/AuthContext';

export const LandingPage: React.FC = () => {
  const { user, isStudent, isAdmin } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="space-y-24 py-6">
      {/* Hero Section */}
      <section className="relative text-center max-w-4xl mx-auto pt-8 pb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5 text-brand-400 animate-pulse" />
          <span>Multi-Signal Academic Collaboration Intelligence</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          Match Students with Faculty Researchers{' '}
          <span className="gradient-text">Through Evidence-Based AI</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed">
          Break down academic silos. Match students to faculty advisors and research labs using 
          dense vector semantic similarity, publication evidence, and skill taxonomy compatibility.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          {user ? (
            isStudent ? (
              <Button
                size="lg"
                onClick={() => navigate('/recommendations')}
                leftIcon={<Sparkles className="w-5 h-5 text-brand-300" />}
                className="glow-brand"
              >
                Run AI Match Engine
              </Button>
            ) : isAdmin ? (
              <Button
                size="lg"
                onClick={() => navigate('/admin')}
                leftIcon={<ShieldCheck className="w-5 h-5" />}
              >
                Open Admin Console
              </Button>
            ) : (
              <Button
                size="lg"
                onClick={() => navigate('/directory')}
                leftIcon={<Compass className="w-5 h-5" />}
              >
                Explore Researchers
              </Button>
            )
          ) : (
            <>
              <Button
                size="lg"
                onClick={() => navigate('/login')}
                leftIcon={<Sparkles className="w-5 h-5 text-brand-300" />}
                className="glow-brand"
              >
                Sign In for Recommendations
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={() => navigate('/directory')}
                leftIcon={<Search className="w-5 h-5" />}
              >
                Browse Faculty Directory
              </Button>
            </>
          )}
        </div>
        {!user && (
          <p className="text-xs text-slate-400 mt-4">
            Demo accounts are not automatically provisioned. Ask your administrator for an account.
          </p>
        )}

        {/* System metrics strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16 pt-10 border-t border-slate-800/80">
          <div>
            <div className="text-2xl font-bold font-mono text-white">4 Signals</div>
            <div className="text-xs text-slate-400 mt-1">Hybrid Reranking Engine</div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-brand-400">384 Dims</div>
            <div className="text-xs text-slate-400 mt-1">Sentence Transformers</div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-emerald-400">100%</div>
            <div className="text-xs text-slate-400 mt-1">Extractive Grounded Explanations</div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-indigo-400">Offline NDCG</div>
            <div className="text-xs text-slate-400 mt-1">Automated IR Benchmarks</div>
          </div>
        </div>
      </section>

      {/* The Problem vs Solution */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card className="border-rose-500/20 bg-rose-950/10">
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4">
            <Zap className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 mb-3">
            The Problem: Fragmented Advising & Keyword Mismatches
          </h2>
          <ul className="space-y-3 text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold shrink-0">✕</span>
              <span><strong>Isolated Lab Websites:</strong> Faculty profiles are outdated, fragmented across departmental pages, or missing active research directions.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold shrink-0">✕</span>
              <span><strong>Keyword Matching Failure:</strong> A student searching "Deep Learning" misses faculty publishing on "Transformer Architectures" or "Neural Operators".</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-rose-400 font-bold shrink-0">✕</span>
              <span><strong>Black-Box Advisor Searches:</strong> Students waste months cold-emailing professors who have no lab capacity or mismatch their project skills.</span>
            </li>
          </ul>
        </Card>

        <Card className="border-emerald-500/20 bg-emerald-950/10">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 mb-3">
            The Solution: Multi-Signal Semantic Alignment
          </h2>
          <ul className="space-y-3 text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold shrink-0">✓</span>
              <span><strong>Dense Vector Retrieval:</strong> Transforms statements of purpose and research biographies into high-dimensional embedding spaces.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold shrink-0">✓</span>
              <span><strong>Publication Evidence:</strong> Aggregates top-K recent publication abstracts to prove active current scholarship.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold shrink-0">✓</span>
              <span><strong>Transparent Reasoning:</strong> Every recommendation breaks down scores across 4 distinct dimensions with lab capacity indicators.</span>
            </li>
          </ul>
        </Card>
      </section>

      {/* 4 Multi-Signal Pillars */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-3">
            Architecture of the Recommendation Engine
          </h2>
          <p className="text-slate-400 text-sm">
            Rather than relying on a single opaque score, our algorithm balances four independent academic evidence channels:
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-brand-500/15 text-brand-400 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white text-base">1. Research Intent</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Cosine similarity between student Statement of Purpose and Faculty holistic narrative profile.
            </p>
            <div className="text-[11px] font-mono text-brand-400 bg-brand-500/10 px-2 py-1 rounded inline-block">
              Weight: 35%
            </div>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white text-base">2. Project Experience</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Measures similarity between student academic project descriptions and faculty publication abstracts.
            </p>
            <div className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded inline-block">
              Weight: 25%
            </div>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/15 text-cyan-400 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white text-base">3. Publication Relevance</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Finds faculty whose recent publications most strongly match the student's stated interests.
            </p>
            <div className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded inline-block">
              Weight: 25%
            </div>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white text-base">4. Skill Compatibility</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Jaccard set overlap across standardized taxonomy nodes (tools, frameworks, methodologies).
            </p>
            <div className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded inline-block">
              Weight: 15%
            </div>
          </Card>
        </div>
      </section>

      {/* Action Banner */}
      <section className="rounded-3xl p-8 sm:p-12 bg-gradient-to-r from-brand-900/60 via-slate-900 to-indigo-950/60 border border-brand-500/30 text-center relative overflow-hidden">
        <div className="relative z-10 max-w-2xl mx-auto space-y-6">
          <h2 className="text-3xl font-extrabold text-white">
            Ready to find your research collaborator?
          </h2>
          <p className="text-slate-300 text-sm">
            Sign in as a student to customize your research interests, add academic projects, and run real-time recommendations.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Button
              size="lg"
              onClick={() => navigate('/login')}
              className="glow-brand"
            >
              Student Sign In
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={() =>
                navigate('/login', { state: { from: { pathname: '/admin' } } })
              }
            >
              Admin Sign In
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};
