import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Building,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Compass,
  Filter,
  Search,
  Users,
} from 'lucide-react';
import { facultyApi } from '../api/faculty';
import { Badge, SyntheticBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { FacultyProfile } from '../types';

export const FacultyDirectory: React.FC = () => {
  const [facultyList, setFacultyList] = useState<FacultyProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [acceptingOnly, setAcceptingOnly] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFaculty = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await facultyApi.listFaculty({
        page,
        page_size: pageSize,
        department: departmentFilter || undefined,
        accepting_students: acceptingOnly ? true : undefined,
        search: searchTerm || undefined,
      });

      setFacultyList(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load faculty directory.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
  }, [page, departmentFilter, acceptingOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchFaculty();
  };

  const departments = [
    'Computer Science',
    'Electrical & Computer Engineering',
    'Data Science & Analytics',
    'Biomedical Informatics',
    'Robotics & Mechanical Engineering',
  ];

  return (
    <div className="space-y-8">
      {/* Directory Title */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium mb-2">
            <Compass className="w-3.5 h-3.5" />
            <span>Faculty Research Profiles</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Researcher & Faculty Directory
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse active university principal investigators, labs, publication records, and mentorship capacities.
          </p>
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Showing {facultyList.length} of {total} researchers
        </div>
      </div>

      {/* Search & Filter Bar */}
      <Card className="p-4">
        <form
          onSubmit={handleSearchSubmit}
          className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center"
        >
          {/* Keyword Search */}
          <div className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              id="faculty-search-input"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by researcher name, lab, or bio keywords..."
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          {/* Department Filter */}
          <div className="md:col-span-4">
            <label htmlFor="faculty-department-filter" className="sr-only">
              Department
            </label>
            <select
              id="faculty-department-filter"
              value={departmentFilter}
              onChange={(e) => {
                setDepartmentFilter(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          {/* Availability Toggle & Submit */}
          <div className="md:col-span-3 flex items-center justify-between gap-2">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={acceptingOnly}
                onChange={(e) => {
                  setAcceptingOnly(e.target.checked);
                  setPage(1);
                }}
                className="rounded border-slate-700 text-brand-600 focus:ring-brand-500"
              />
              <span>Accepting Only</span>
            </label>

            <Button type="submit" size="sm" variant="secondary">
              Filter
            </Button>
          </div>
        </form>
      </Card>

      {/* Faculty Cards Grid */}
      {isLoading ? (
        <LoadingSpinner message="Searching verified faculty records..." size="lg" />
      ) : error ? (
        <EmptyState
          icon={<Filter className="w-8 h-8 text-rose-400" />}
          title="Failed to Load Researchers"
          description={error}
          actionText="Retry Search"
          onAction={fetchFaculty}
        />
      ) : facultyList.length === 0 ? (
        <EmptyState
          icon={<Compass className="w-8 h-8 text-slate-500" />}
          title="No Researchers Found"
          description="Try broadening your department or keyword search filters."
          actionText="Clear Filters"
          onAction={() => {
            setSearchTerm('');
            setDepartmentFilter('');
            setAcceptingOnly(false);
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {facultyList.map((fac) => {
            const isSynthetic =
              fac.faculty_number?.startsWith('SYNTH') ||
              fac.bio?.includes('[SYNTHETIC]');
            const availableSlots = fac.max_capacity - fac.current_student_count;

            return (
              <Card
                key={fac.id}
                hoverEffect
                className="flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="font-bold text-base text-white hover:text-brand-300 transition-colors">
                        {fac.first_name} {fac.last_name}
                      </h3>
                      <div className="text-xs text-slate-400 font-medium">
                        {fac.title_rank.replace(/_/g, ' ')}
                      </div>
                    </div>
                    {isSynthetic && <SyntheticBadge />}
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-3">
                    <Building className="w-3.5 h-3.5 text-slate-500" />
                    <span>{fac.department}</span>
                  </div>

                  {fac.lab_name && (
                    <div className="text-xs text-brand-300/90 font-medium mb-3 bg-brand-500/10 px-2.5 py-1 rounded-md border border-brand-500/20 truncate">
                      {fac.lab_name}
                    </div>
                  )}

                  {fac.bio && (
                    <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 mb-4">
                      {fac.bio}
                    </p>
                  )}
                </div>

                <div className="pt-4 border-t border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-slate-400">
                      <Users className="w-3.5 h-3.5" />
                      Lab Capacity:
                    </span>
                    <span
                      className={`font-mono font-medium ${
                        availableSlots > 0 ? 'text-emerald-400' : 'text-slate-500'
                      }`}
                    >
                      {availableSlots > 0 ? `${availableSlots} openings` : 'Full'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <Badge
                      variant={fac.accepting_students ? 'success' : 'neutral'}
                      size="sm"
                    >
                      {fac.accepting_students ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" /> Accepting
                        </>
                      ) : (
                        'Not Accepting'
                      )}
                    </Badge>

                    <Link
                      to={`/faculty/${fac.id}`}
                      aria-label={`View ${fac.first_name} ${fac.last_name} profile`}
                      className="text-xs text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
                    >
                      View Profile <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-6 border-t border-slate-800">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            leftIcon={<ChevronLeft className="w-4 h-4" />}
          >
            Previous
          </Button>

          <span className="text-xs text-slate-400 font-mono">
            Page {page} of {totalPages}
          </span>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page === totalPages}
            rightIcon={<ChevronRight className="w-4 h-4" />}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};
