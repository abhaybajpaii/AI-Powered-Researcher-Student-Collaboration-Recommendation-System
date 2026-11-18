export type Role = 'STUDENT' | 'FACULTY' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  student_id?: string | null;
  faculty_id?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  full_name?: string | null;
  department?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TopicSkill {
  id: string;
  name: string;
  slug: string;
  category: 'RESEARCH_TOPIC' | 'METHODOLOGY' | 'TECHNICAL_SKILL' | 'DOMAIN';
  parent_id?: string | null;
  description?: string | null;
}

export interface StudentSkillInterest {
  id: string;
  topic_skill_id: string;
  proficiency_level: number;
  interest_level: number;
  years_experience?: number;
  topic_skill?: TopicSkill;
}

export interface AcademicProject {
  id: string;
  student_id: string;
  title: string;
  description: string;
  role?: string | null;
  github_url?: string | null;
}

export interface StudentProfile {
  id: string;
  user_id: string;
  student_number?: string | null;
  first_name: string;
  last_name: string;
  department: string;
  degree_level: string; // UNDERGRADUATE, MASTERS, PHD
  gpa_or_standing?: number | null;
  graduation_year?: number | null;
  bio?: string | null;
  statement_of_purpose: string;
  availability_status: string; // SEEKING_ADVISOR, OPEN_TO_PROJECTS, NOT_AVAILABLE
  skills_interests: StudentSkillInterest[];
  academic_projects: AcademicProject[];
  created_at: string;
  updated_at: string;
}

export interface Publication {
  id: string;
  title: string;
  abstract?: string | null;
  publication_year?: number | null;
  venue?: string | null;
  doi?: string | null;
  citation_count?: number;
  url?: string | null;
  author_names?: string[];
}

export interface PublicationAuthorship {
  id: string;
  publication_id: string;
  faculty_id: string;
  author_order: number;
  raw_author_name: string;
  publication: Publication;
}

export interface FacultySkillExpertise {
  id: string;
  topic_skill_id: string;
  expertise_level: number;
  is_primary_focus: boolean;
  topic_skill?: TopicSkill;
}

export interface FacultyProfile {
  id: string;
  user_id: string;
  faculty_number?: string | null;
  first_name: string;
  last_name: string;
  department: string;
  title_rank: string;
  office_location?: string | null;
  website_url?: string | null;
  lab_name?: string | null;
  accepting_students: boolean;
  max_capacity: number;
  current_student_count: number;
  bio?: string | null;
  is_synthetic?: boolean;
  verification_status?: string;
  openalex_id?: string | null;
  institution_name?: string | null;
  institution_ror?: string | null;
  verification_notes?: string | null;
  verified_at?: string | null;
  skills_expertise: FacultySkillExpertise[];
  authorship_links: PublicationAuthorship[];
  created_at: string;
  updated_at: string;
}

export interface ScoreBreakdown {
  research_interest_score: number;
  project_research_score: number;
  publication_relevance_score: number;
  skill_compatibility_score: number;
  normalized_weights: {
    research_interest?: number;
    project_research?: number;
    publication_relevance?: number;
    skill_compatibility?: number;
    [key: string]: number | undefined;
  };
  weights?: {
    research_interest?: number;
    project_research?: number;
    publication_relevance?: number;
    skill_compatibility?: number;
    [key: string]: number | undefined;
  };
}

export interface PublicationEvidence {
  publication_id: string;
  title: string;
  similarity_score: number;
  year?: number | null;
  publication_year?: number | null;
  venue?: string | null;
  relevant_excerpt?: string;
}

export interface RecommendationItem {
  faculty_id: string;
  faculty_name: string;
  department: string;
  lab_name?: string | null;
  title_rank: string;
  accepting_students?: boolean;
  open_capacity?: number;
  rank_position: number;
  rank?: number;
  overall_score: number;
  total_score?: number;
  score_breakdown: ScoreBreakdown;
  top_publications: PublicationEvidence[];
  relevant_publications?: PublicationEvidence[];
  shared_skills: string[];
  explanation_summary: string;
  missing_data_caveats: string[];
  caveats?: string[];
  is_synthetic?: boolean;
  verification_status?: string;
  openalex_id?: string | null;
  institution_name?: string | null;
}

export interface RecommendationResponse {
  run_id: string;
  student_id: string;
  algorithm_version: string;
  execution_time_ms: number;
  total_candidates_evaluated: number;
  recommendations: RecommendationItem[];
}

export interface RecommendationHistoryItem {
  run_id: string;
  algorithm_version: string;
  execution_time_ms: number;
  created_at: string;
}

export interface RecommendationHistoryResponse {
  student_id: string;
  total_runs: number;
  runs: RecommendationHistoryItem[];
}

export interface RecommendationRunSummary {
  id?: string;
  run_id?: string;
  student_id?: string;
  algorithm_version: string;
  execution_time_ms: number;
  total_candidates?: number;
  created_at: string;
  results?: RecommendationItem[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface ImportJob {
  id: string;
  data_source_id?: string;
  data_source_name?: string;
  data_source_type?: string;
  status: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  error_log?: unknown[] | null;
  started_at: string | null;
  completed_at?: string | null;
}

export interface DataCountsResponse {
  summary: {
    total_records: number;
    synthetic_records: number;
    real_records: number;
  };
  by_entity: Record<
    string,
    { total: number; synthetic: number; real: number }
  >;
}

export interface EvaluationBenchmarkResponse {
  benchmark_suite: string;
  status?: 'NO_JUDGMENTS_FOUND' | 'NO_VALID_QUERIES';
  message?: string;
  queries_evaluated?: number;
  total_judgments?: number;
  hybrid_embedding_scores?: Record<string, number>;
  tfidf_baseline_scores?: Record<string, number>;
  comparison?: Record<
    string,
    {
      hybrid_embedding: number;
      tfidf_baseline: number;
      relative_lift_percent: string;
    }
  >;
  limitations_and_caveats?: string[];
}

export interface EmbeddingStatsResponse {
  total_embeddings: number;
  by_entity_type: Record<string, number>;
  by_model: { model_name: string; model_version: string; count: number }[];
  active_model: string;
  active_dimension: number;
}
