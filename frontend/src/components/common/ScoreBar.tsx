import React from 'react';

interface ScoreBarProps {
  label: string;
  score: number; // 0 to 1
  weight?: number;
  showPercentage?: boolean;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
  label,
  score,
  weight,
  showPercentage = true,
}) => {
  const percentage = Math.round(Math.min(Math.max(score, 0), 1) * 100);

  // Gradient color based on score magnitude
  let barGradient = 'from-brand-600 to-indigo-500';
  let badgeColor = 'text-brand-300';
  if (percentage >= 80) {
    barGradient = 'from-emerald-500 to-teal-400';
    badgeColor = 'text-emerald-400';
  } else if (percentage >= 60) {
    barGradient = 'from-brand-500 to-violet-500';
    badgeColor = 'text-brand-300';
  } else if (percentage >= 40) {
    barGradient = 'from-amber-500 to-orange-400';
    badgeColor = 'text-amber-400';
  } else {
    barGradient = 'from-slate-600 to-slate-500';
    badgeColor = 'text-slate-400';
  }

  return (
    <div className="w-full">
      <div className="flex justify-between items-center text-xs mb-1.5">
        <span className="font-medium text-slate-300 flex items-center gap-1.5">
          {label}
          {weight !== undefined && (
            <span className="text-[10px] text-slate-500 font-mono">
              (w={(weight * 100).toFixed(0)}%)
            </span>
          )}
        </span>
        {showPercentage && (
          <span className={`font-mono font-semibold ${badgeColor}`}>
            {percentage}%
          </span>
        )}
      </div>
      <div className="w-full h-2 rounded-full bg-slate-800/80 overflow-hidden p-0.5 border border-slate-700/50">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-700 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
