import React from 'react';
import { Database, GitBranch, Shield, Sparkles } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 text-slate-400 py-12 px-4 sm:px-6 lg:px-8 mt-auto">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        <div className="space-y-3">
          <div className="text-white font-bold text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-400" />
            CollabMatch Architecture
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            AI-driven researcher-student matching with PostgreSQL pgvector, Sentence Transformers, and multi-signal hybrid reranking.
          </p>
        </div>

        <div>
          <h4 className="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-3">
            Matching Signals
          </h4>
          <ul className="text-xs space-y-2">
            <li className="text-slate-400 hover:text-slate-200">Semantic Research Intent (MiniLM-L6-v2)</li>
            <li className="text-slate-400 hover:text-slate-200">Applied Project Alignment</li>
            <li className="text-slate-400 hover:text-slate-200">Top-K Publication Abstract Relevance</li>
            <li className="text-slate-400 hover:text-slate-200">Jaccard Skill Compatibility</li>
          </ul>
        </div>

        <div>
          <h4 className="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-3">
            Data & Provenance
          </h4>
          <ul className="text-xs space-y-2">
            <li className="flex items-center gap-1.5 text-slate-400">
              <Database className="w-3.5 h-3.5 text-brand-400" />
              PostgreSQL + pgvector HNSW
            </li>
            <li className="flex items-center gap-1.5 text-slate-400">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              Isolated Synthetic Benchmarks
            </li>
            <li className="flex items-center gap-1.5 text-slate-400">
              <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
              OpenAlex / S2 Connector Ready
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-3">
            Offline Benchmarks
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluated continuously against NDCG@K, Precision@K, Recall@K, and MRR relevance judgments.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
        <p>© 2026 Academic AI Collaboration Recommendation System. Built with FastAPI, pgvector & React.</p>
        <p className="mt-2 sm:mt-0 font-mono text-[11px]">System Status: Operational</p>
      </div>
    </footer>
  );
};
