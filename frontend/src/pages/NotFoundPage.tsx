import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Compass, Home } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="w-16 h-16 rounded-3xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mb-6">
        <AlertCircle className="w-8 h-8" />
      </div>

      <h1 className="text-4xl font-extrabold text-white mb-2">404 — Page Not Found</h1>
      <p className="text-sm text-slate-400 max-w-md mb-8 leading-relaxed">
        The requested URL could not be resolved. If an entity was deleted or a link was moved, you can return to the platform directory or your student dashboard.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button
          variant="primary"
          onClick={() => navigate('/')}
          leftIcon={<Home className="w-4 h-4" />}
        >
          Return Home
        </Button>
        <Button
          variant="secondary"
          onClick={() => navigate('/directory')}
          leftIcon={<Compass className="w-4 h-4" />}
        >
          Browse Researchers
        </Button>
      </div>
    </div>
  );
};
