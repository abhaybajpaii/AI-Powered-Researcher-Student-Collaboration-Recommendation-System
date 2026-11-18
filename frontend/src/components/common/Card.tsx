import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  glass?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverEffect = false,
  glass = true,
  className = '',
  ...props
}) => {
  const baseClasses = 'rounded-xl p-6 transition-all duration-200 border';
  const glassClasses = glass
    ? 'bg-slate-900/60 backdrop-blur-md border-slate-800/80 shadow-lg shadow-black/20'
    : 'bg-slate-900 border-slate-800';
  const hoverClasses = hoverEffect
    ? 'hover:border-brand-500/30 hover:bg-slate-850 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-brand-500/5'
    : '';

  return (
    <div
      className={`${baseClasses} ${glassClasses} ${hoverClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
