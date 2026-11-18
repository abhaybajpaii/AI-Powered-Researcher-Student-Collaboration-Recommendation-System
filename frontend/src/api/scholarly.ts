import { apiClient } from './client';
import { ImportJob } from '../types';

export interface ScholarlyWorkPreview {
  openalex_id: string;
  title: string;
  abstract: string;
  publication_year: number | null;
  venue: string | null;
  doi: string | null;
  citation_count: number;
  url: string | null;
  authors: Array<{ name: string; openalex_id?: string; institutions?: string[] }>;
  topics: string[];
}

export interface ScholarlyAuthorPreview {
  openalex_id: string;
  display_name: string;
  first_name: string;
  last_name: string;
  works_count: number;
  cited_by_count: number;
  institution_name: string | null;
  institution_ror: string | null;
  orcid?: string | null;
  topics: string[];
}

export interface ScholarlyDataSummary {
  faculty: {
    real_count: number;
    synthetic_count: number;
    total: number;
    by_verification_status: Record<string, number>;
  };
  publications: {
    real_count: number;
    synthetic_count: number;
    total: number;
  };
}

export interface VerificationFacultyItem {
  id: string;
  first_name: string;
  last_name: string;
  department: string;
  title_rank: string;
  lab_name: string | null;
  accepting_students: boolean;
  is_synthetic: boolean;
  verification_status: string;
  openalex_id: string | null;
  institution_name: string | null;
  verification_notes: string | null;
  verified_at: string | null;
}

export const scholarlyApi = {
  searchWorks: async (
    query: string,
    institution_ror?: string,
    year?: number,
    page: number = 1,
    per_page: number = 10
  ) => {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      per_page: per_page.toString(),
    });
    if (institution_ror) params.append('institution_ror', institution_ror);
    if (year) params.append('year', year.toString());

    return apiClient.get<{
      total_count: number;
      page: number;
      per_page: number;
      results: ScholarlyWorkPreview[];
    }>(`/scholarly/search/works?${params.toString()}`);
  },

  searchAuthors: async (
    query: string,
    institution_ror?: string,
    page: number = 1,
    per_page: number = 10
  ) => {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      per_page: per_page.toString(),
    });
    if (institution_ror) params.append('institution_ror', institution_ror);

    return apiClient.get<{
      total_count: number;
      page: number;
      per_page: number;
      results: ScholarlyAuthorPreview[];
    }>(`/scholarly/search/authors?${params.toString()}`);
  },

  searchInstitutions: async (query: string) => {
    return apiClient.get<Array<{
      openalex_id: string;
      display_name: string;
      ror: string | null;
      country_code: string | null;
      works_count: number;
    }>>(`/scholarly/search/institutions?query=${encodeURIComponent(query)}`);
  },

  lookupCrossref: async (doi: string) => {
    return apiClient.get<any>(`/scholarly/crossref/${encodeURIComponent(doi)}`);
  },

  importWorks: async (
    works: ScholarlyWorkPreview[],
    enrich_crossref: boolean = true,
    auto_embed: boolean = true
  ) => {
    return apiClient.post<{
      job_id: string;
      status: string;
      processed: number;
      created: number;
      updated: number;
      errors: any[];
    }>('/scholarly/import/works', {
      works,
      enrich_crossref,
      auto_embed,
    });
  },

  importAuthors: async (
    authors: ScholarlyAuthorPreview[],
    default_department: string = 'Computer Science',
    default_status: string = 'PENDING_REVIEW',
    auto_embed: boolean = true
  ) => {
    return apiClient.post<{
      job_id: string;
      status: string;
      processed: number;
      created: number;
      updated: number;
      errors: any[];
    }>('/scholarly/import/authors', {
      authors,
      default_department,
      default_status,
      auto_embed,
    });
  },

  importCsv: async (csv_text: string, auto_embed: boolean = true) => {
    return apiClient.post<{
      job_id: string;
      status: string;
      processed: number;
      created: number;
      updated: number;
      errors: any[];
    }>('/scholarly/import/csv', {
      csv_text,
      auto_embed,
    });
  },

  getSummary: async () => {
    return apiClient.get<ScholarlyDataSummary>('/scholarly/summary');
  },

  getJobs: async (limit: number = 20): Promise<ImportJob[]> => {
    return apiClient.get<ImportJob[]>(`/scholarly/jobs?limit=${limit}`);
  },

  retryJob: async (job_id: string) => {
    return apiClient.post<{ status: string; job_id: string }>(`/scholarly/jobs/${job_id}/retry`, {});
  },

  listVerificationFaculty: async (params?: {
    status_filter?: string;
    is_synthetic?: boolean;
    department?: string;
    page?: number;
    per_page?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.status_filter) sp.append('status_filter', params.status_filter);
    if (params?.is_synthetic !== undefined) sp.append('is_synthetic', params.is_synthetic.toString());
    if (params?.department) sp.append('department', params.department);
    if (params?.page) sp.append('page', params.page.toString());
    if (params?.per_page) sp.append('per_page', params.per_page.toString());

    return apiClient.get<{
      total: number;
      page: number;
      per_page: number;
      items: VerificationFacultyItem[];
    }>(`/scholarly/verification/faculty?${sp.toString()}`);
  },

  updateVerification: async (
    faculty_id: string,
    payload: {
      verification_status: string;
      verification_notes?: string;
      department?: string;
      title_rank?: string;
      accepting_students?: boolean;
    }
  ) => {
    return apiClient.put<{
      status: string;
      faculty_id: string;
      verification_status: string;
      verified_at: string | null;
    }>(`/scholarly/verification/faculty/${faculty_id}`, payload);
  },

  batchVerification: async (
    faculty_ids: string[],
    action: 'VERIFY' | 'REJECT',
    notes?: string
  ) => {
    return apiClient.post<{
      action: string;
      updated_count: number;
      new_status: string;
    }>('/scholarly/verification/faculty/batch', {
      faculty_ids,
      action,
      notes,
    });
  },
};
