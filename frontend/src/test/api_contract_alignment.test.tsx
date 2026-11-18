import React from 'react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { recommendationsApi } from '../api/recommendations';
import { studentsApi } from '../api/students';
import { StudentDashboard } from '../pages/StudentDashboard';
import { RecommendationResults } from '../pages/RecommendationResults';
import { RecommendationResponse, StudentProfile } from '../types';

// Mock AuthContext hook
const mockAuthValue = {
  user: {
    id: 'user-1',
    email: 'student@university.edu',
    role: 'STUDENT',
    is_active: true,
    student_id: 'student-123',
  },
  token: 'mock-jwt-token',
  studentId: 'student-123',
  facultyId: null,
  isAdmin: false,
  isStudent: true,
  isFaculty: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
};

vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockAuthValue,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockStudentProfile: StudentProfile = {
  id: 'student-123',
  user_id: 'user-1',
  student_number: 'STU1001',
  first_name: 'Ada',
  last_name: 'Lovelace',
  department: 'Computer Science',
  degree_level: 'PHD',
  gpa_or_standing: 3.95,
  graduation_year: 2026,
  bio: 'Interested in algorithmic foundations and machine learning.',
  statement_of_purpose: 'Developing verifiable neural networks for autonomous decision-making.',
  availability_status: 'SEEKING_ADVISOR',
  skills_interests: [],
  academic_projects: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockBackendRecommendationResponse: RecommendationResponse = {
  run_id: 'run-123',
  student_id: 'student-123',
  algorithm_version: 'hybrid_v1',
  execution_time_ms: 38.5,
  total_candidates_evaluated: 250,
  recommendations: [
    {
      faculty_id: 'fac-456',
      faculty_name: 'Dr. Alan Turing',
      department: 'Computer Science',
      title_rank: 'PROFESSOR',
      lab_name: 'Theoretical Computing Group',
      accepting_students: true,
      open_capacity: 2,
      rank_position: 1,
      overall_score: 0.91,
      score_breakdown: {
        research_interest_score: 0.95,
        project_research_score: 0.88,
        publication_relevance_score: 0.90,
        skill_compatibility_score: 0.85,
        normalized_weights: {
          research_interest: 0.40,
          project_research: 0.30,
          publication_relevance: 0.20,
          skill_compatibility: 0.10,
        },
      },
      top_publications: [
        {
          publication_id: 'pub-999',
          title: 'Computing Machinery and Intelligence',
          year: 2024,
          venue: 'Mind & Machines',
          similarity_score: 0.94,
          relevant_excerpt: 'Can machines think? Analyzing foundations of symbolic and dense architectures.',
        },
      ],
      shared_skills: ['Algorithms', 'Machine Learning'],
      explanation_summary: 'Exceptional theoretical synergy between student statement and laboratory publications.',
      missing_data_caveats: [
        'Student profile has no verified code repository links.',
      ],
      is_synthetic: false,
      verification_status: 'VERIFIED',
    },
  ],
};

describe('API Contract Alignment Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // 1. Feedback request URL and query parameters
  // ---------------------------------------------------------------------------
  it('Task 1: submits feedback with rating and notes as URL query parameters', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        status: 'feedback_recorded',
        run_id: 'run-123',
        faculty_id: 'fac-456',
        rating: 5,
      }),
    });
    globalThis.fetch = fetchMock;

    await recommendationsApi.submitFeedback(
      'run-123',
      'fac-456',
      5,
      'Excellent multi-signal match'
    );

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    const calledOptions = fetchMock.mock.calls[0][1];

    // Verify URL contains rating and encoded notes query parameters
    expect(calledUrl).toContain('/recommendations/runs/run-123/results/fac-456/feedback');
    expect(calledUrl).toContain('rating=5');
    expect(calledUrl).toContain('notes=Excellent+multi-signal+match');

    // Verify method is POST and request body is empty (not JSON body)
    expect(calledOptions.method).toBe('POST');
    expect(calledOptions.body).toBeUndefined();
  });

  it('Task 1: submits feedback with rating only when notes are omitted', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        status: 'feedback_recorded',
        run_id: 'run-123',
        faculty_id: 'fac-456',
        rating: 4,
      }),
    });
    globalThis.fetch = fetchMock;

    await recommendationsApi.submitFeedback('run-123', 'fac-456', 4);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('rating=4');
    expect(calledUrl).not.toContain('notes=');
  });

  // ---------------------------------------------------------------------------
  // 2. History response with runs
  // ---------------------------------------------------------------------------
  it('Task 2: consumes backend recommendation history object and renders runs on dashboard', async () => {
    vi.spyOn(studentsApi, 'getStudent').mockResolvedValue(mockStudentProfile);
    vi.spyOn(recommendationsApi, 'getHistory').mockResolvedValue({
      student_id: 'student-123',
      total_runs: 1,
      runs: [
        {
          run_id: 'run-alpha',
          algorithm_version: 'hybrid_v1',
          execution_time_ms: 42.6,
          created_at: '2026-11-05T01:00:00Z',
        },
      ],
    });

    render(
      <MemoryRouter>
        <StudentDashboard />
      </MemoryRouter>
    );

    // Verify dashboard renders the past run
    await waitFor(() => {
      expect(screen.getByText('hybrid_v1')).toBeInTheDocument();
      expect(screen.getByText('42.6 ms')).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // 3. Empty recommendation history
  // ---------------------------------------------------------------------------
  it('Task 2: safely handles empty recommendation history without throwing', async () => {
    vi.spyOn(studentsApi, 'getStudent').mockResolvedValue(mockStudentProfile);
    vi.spyOn(recommendationsApi, 'getHistory').mockResolvedValue({
      student_id: 'student-123',
      total_runs: 0,
      runs: [],
    });

    render(
      <MemoryRouter>
        <StudentDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No recommendation runs yet/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Generate First Match/i })).toBeInTheDocument();
    });
  });

  it('Task 2: displays a retryable unavailable state when history loading fails', async () => {
    const historySpy = vi
      .spyOn(recommendationsApi, 'getHistory')
      .mockRejectedValue(new Error('history request failed'));
    vi.spyOn(studentsApi, 'getStudent').mockResolvedValue(mockStudentProfile);

    render(
      <MemoryRouter>
        <StudentDashboard />
      </MemoryRouter>
    );

    expect(
      await screen.findByText(/Recommendation history is unavailable: history request failed/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/No recommendation runs yet/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Retry History/i }));
    await waitFor(() => expect(historySpy).toHaveBeenCalledTimes(2));
  });

  // ---------------------------------------------------------------------------
  // 4. Recommendation score breakdown rendering
  // ---------------------------------------------------------------------------
  it('Task 3: renders recommendation scores using normalized_weights and overall_score', async () => {
    vi.spyOn(recommendationsApi, 'generate').mockResolvedValue(mockBackendRecommendationResponse);

    render(
      <MemoryRouter>
        <RecommendationResults />
      </MemoryRouter>
    );

    // Wait for recommendation item to render
    await waitFor(() => {
      expect(screen.getByText('Dr. Alan Turing')).toBeInTheDocument();
    });

    // Verify overall score percentage (0.91 -> 91%)
    expect(screen.getByText('91%')).toBeInTheDocument();

    // Verify score breakdown labels and weights from normalized_weights
    expect(screen.getByText('Research Intent')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('(w=40%)')).toBeInTheDocument();

    expect(screen.getByText('Project Experience')).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();
    expect(screen.getByText('(w=30%)')).toBeInTheDocument();

    expect(screen.getByText('Publication Match')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('(w=20%)')).toBeInTheDocument();

    expect(screen.getByText('Skill Compatibility')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('(w=10%)')).toBeInTheDocument();
  });

  it('sends the newly selected data mode when filtering recommendation results', async () => {
    const generateSpy = vi
      .spyOn(recommendationsApi, 'generate')
      .mockResolvedValue(mockBackendRecommendationResponse);

    render(
      <MemoryRouter>
        <RecommendationResults />
      </MemoryRouter>
    );

    await waitFor(() => expect(generateSpy).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: /Real Research Only/i }));

    await waitFor(() => {
      expect(generateSpy).toHaveBeenLastCalledWith(
        expect.objectContaining({
          filters: expect.objectContaining({ data_mode: 'REAL_ONLY' }),
        })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // 5. Publication evidence rendering
  // ---------------------------------------------------------------------------
  it('Task 3: renders publication evidence modal with year, venue, and excerpt', async () => {
    vi.spyOn(recommendationsApi, 'generate').mockResolvedValue(mockBackendRecommendationResponse);

    render(
      <MemoryRouter>
        <RecommendationResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Inspect Evidence \(1 papers\)/i)).toBeInTheDocument();
    });

    // Open evidence modal
    fireEvent.click(screen.getByText(/Inspect Evidence \(1 papers\)/i));

    // Verify evidence modal contents
    await waitFor(() => {
      expect(screen.getByText('Evidence Breakdown: Dr. Alan Turing')).toBeInTheDocument();
      expect(screen.getByText('Computing Machinery and Intelligence')).toBeInTheDocument();
      expect(screen.getByText(/Mind & Machines \(2024\)/i)).toBeInTheDocument();
      expect(screen.getByText('94% match')).toBeInTheDocument();
      expect(
        screen.getByText(/"Can machines think\? Analyzing foundations of symbolic and dense architectures\."/i)
      ).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // 6. Missing-data caveat rendering
  // ---------------------------------------------------------------------------
  it('Task 3: renders missing_data_caveats with alert icons', async () => {
    vi.spyOn(recommendationsApi, 'generate').mockResolvedValue(mockBackendRecommendationResponse);

    render(
      <MemoryRouter>
        <RecommendationResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText('Student profile has no verified code repository links.')
      ).toBeInTheDocument();
    });
  });
});
