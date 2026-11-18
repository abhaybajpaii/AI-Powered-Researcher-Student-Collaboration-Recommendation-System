import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  const variantStyles = {
    primary: 'bg-brand-500/15 text-brand-300 border border-brand-500/30',
    success: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    warning: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
    danger: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
    info: 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30',
    neutral: 'bg-slate-800 text-slate-300 border border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

export const SyntheticBadge: React.FC<{ className?: string }> = ({ className = '' }) => (
  <Badge
    variant="warning"
    size="sm"
    className={`font-mono text-[10px] tracking-wide uppercase ${className}`}
  >
    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse inline-block" />
    Synthetic Demo
  </Badge>
);

export const RealDataBadge: React.FC<{ source?: string; className?: string }> = ({
  source = 'OpenAlex',
  className = '',
}) => (
  <Badge
    variant="info"
    size="sm"
    className={`font-mono text-[10px] tracking-wide uppercase ${className}`}
  >
    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 inline-block" />
    Real: {source}
  </Badge>
);

export const VerificationBadge: React.FC<{ status?: string; className?: string }> = ({
  status = 'UNVERIFIED',
  className = '',
}) => {
  const norm = status.toUpperCase();
  if (norm === 'VERIFIED') {
    return (
      <Badge variant="success" size="sm" className={className}>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
        Verified Faculty
      </Badge>
    );
  }
  if (norm === 'PENDING_REVIEW') {
    return (
      <Badge variant="warning" size="sm" className={className}>
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
        Pending Review
      </Badge>
    );
  }
  if (norm === 'REJECTED_OUTDATED') {
    return (
      <Badge variant="danger" size="sm" className={className}>
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
        Rejected / Outdated
      </Badge>
    );
  }
  return (
    <Badge variant="neutral" size="sm" className={className}>
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 inline-block" />
      Unverified Author
    </Badge>
  );
};

