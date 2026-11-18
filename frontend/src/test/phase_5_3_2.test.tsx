import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { StudentProfileEditor } from '../pages/StudentProfileEditor';
import { FacultyDirectory } from '../pages/FacultyDirectory';
import { AdminDashboard } from '../pages/AdminDashboard';
import { FacultyProfile, StudentProfile } from '../types';

const mocks = vi.hoisted(() => ({
  register: vi.fn(),
  login: vi.fn(),
  getStudent: vi.fn(),
  updateStudent: vi.fn(),
  listTopics: vi.fn(),
  listFaculty: vi.fn(),
  getDataCounts: vi.fn(),
  getJobs: vi.fn(),
  getStats: vi.fn(),
  getSummary: vi.fn(),
  listVerificationFaculty: vi.fn(),
  retryJob: vi.fn(),
  unused: vi.fn(),
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    studentId: 'student-123',
    facultyId: null,
    isStudent: false,
    isAdmin: false,
    isFaculty: false,
    register: mocks.register,
    login: mocks.login,
    logout: vi.fn(),
    refreshUser: vi.fn(),
  }),
}));

vi.mock('../api/students', () => ({
  studentsApi: {
    getStudent: mocks.getStudent,
    updateStudent: mocks.updateStudent,
    listStudents: mocks.unused,
    addProject: mocks.unused,
    deleteProject: mocks.unused,
    addSkill: mocks.unused,
    deleteSkill: mocks.unused,
  },
}));

vi.mock('../api/taxonomy', () => ({
  taxonomyApi: { listTopics: mocks.listTopics },
}));

vi.mock('../api/faculty', () => ({
  facultyApi: { listFaculty: mocks.listFaculty },
}));

vi.mock('../api/admin', () => ({
  adminApi: {
    getDataCounts: mocks.getDataCounts,
    seedSynthetic: mocks.unused,
    resetSynthetic: mocks.unused,
  },
}));

vi.mock('../api/embeddings', () => ({
  embeddingsApi: { getStats: mocks.getStats, syncAll: mocks.unused },
}));

vi.mock('../api/evaluation', () => ({
  evaluationApi: { runBenchmark: mocks.unused },
}));

vi.mock('../api/scholarly', () => ({
  scholarlyApi: {
    getJobs: mocks.getJobs,
    getSummary: mocks.getSummary,
    listVerificationFaculty: mocks.listVerificationFaculty,
    searchWorks: mocks.unused,
    searchAuthors: mocks.unused,
    importWorks: mocks.unused,
    importAuthors: mocks.unused,
    importCsv: mocks.unused,
    updateVerification: mocks.unused,
    retryJob: mocks.retryJob,
  },
}));

const studentProfile: StudentProfile = {
  id: 'student-123',
  user_id: 'user-123',
  student_number: 'STU1001',
  first_name: 'Ada',
  last_name: 'Lovelace',
  department: 'Computer Science',
  degree_level: 'PHD',
  gpa_or_standing: 3.95,
  graduation_year: 2027,
  bio: 'Researcher',
  statement_of_purpose: 'Researching useful computing systems.',
  availability_status: 'SEEKING_ADVISOR',
  skills_interests: [],
  academic_projects: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const facultyProfile: FacultyProfile = {
  id: 'faculty-123',
  user_id: 'user-456',
  faculty_number: null,
  first_name: 'Grace',
  last_name: 'Hopper',
  department: 'Computer Science',
  title_rank: 'PROFESSOR',
  office_location: null,
  website_url: null,
  lab_name: 'Compilers Lab',
  accepting_students: true,
  max_capacity: 3,
  current_student_count: 1,
  bio: 'Research on compilers.',
  skills_expertise: [],
  authorship_links: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const renderRegister = () =>
  render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/student/dashboard" element={<p>Student dashboard destination</p>} />
      </Routes>
    </MemoryRouter>
  );

const fillRegistrationForm = () => {
  fireEvent.change(screen.getByLabelText('First Name'), { target: { value: 'Ada' } });
  fireEvent.change(screen.getByLabelText('Last Name'), { target: { value: 'Lovelace' } });
  fireEvent.change(screen.getByLabelText('University Email'), {
    target: { value: 'ada@example.edu' },
  });
  fireEvent.change(screen.getByLabelText('Department'), {
    target: { value: 'Computer Science' },
  });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
  fireEvent.change(screen.getByLabelText('Confirm Password'), {
    target: { value: 'password123' },
  });
};

describe('Phase 5.3.2 frontend regressions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.register.mockResolvedValue(undefined);
    mocks.login.mockResolvedValue(undefined);
    mocks.getStudent.mockResolvedValue(studentProfile);
    mocks.updateStudent.mockImplementation(async (_id: string, updates: Partial<StudentProfile>) => ({
      ...studentProfile,
      ...updates,
    }));
    mocks.listTopics.mockResolvedValue([]);
    mocks.listFaculty.mockResolvedValue({
      items: [facultyProfile],
      total: 1,
      page: 1,
      page_size: 12,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    });
    mocks.getDataCounts.mockResolvedValue({
      summary: { total_records: 0, synthetic_records: 0, real_records: 0 },
      by_entity: {},
    });
    mocks.getJobs.mockResolvedValue([]);
    mocks.getStats.mockResolvedValue({
      total_embeddings: 0,
      by_entity_type: {},
      by_model: [],
      active_model: 'test-model',
      active_dimension: 384,
    });
    mocks.getSummary.mockResolvedValue({
      faculty: { real_count: 0, synthetic_count: 0, total: 0, by_verification_status: {} },
      publications: { real_count: 0, synthetic_count: 0, total: 0 },
    });
    mocks.listVerificationFaculty.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 50 });
  });

  it('keeps student registration working and blocks unsupported faculty self-registration', async () => {
    const { unmount } = renderRegister();
    fillRegistrationForm();
    fireEvent.click(screen.getByRole('button', { name: /Create Account & Profile/i }));

    await waitFor(() => {
      expect(mocks.register).toHaveBeenCalledWith(
        expect.objectContaining({ role: 'STUDENT', email: 'ada@example.edu' })
      );
    });
    expect(await screen.findByText('Student dashboard destination')).toBeInTheDocument();

    unmount();
    mocks.register.mockClear();
    renderRegister();
    fillRegistrationForm();
    fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'FACULTY' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Account & Profile/i }));

    expect(
      await screen.findByText(/Faculty accounts must be created through the supported faculty onboarding process/i)
    ).toBeInTheDocument();
    expect(mocks.register).not.toHaveBeenCalled();
  });

  it('exposes programmatic names for login and registration fields', () => {
    const { unmount } = render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    expect(screen.getByLabelText('University Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();

    unmount();
    renderRegister();
    for (const label of [
      'First Name',
      'Last Name',
      'University Email',
      'Role',
      'Department',
      'Statement of Research Purpose',
      'Password',
      'Confirm Password',
    ]) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
  });

  it('routes an admin login to the admin console by default', async () => {
    mocks.login.mockResolvedValue({ role: 'ADMIN' });
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/admin" element={<p>Admin dashboard destination</p>} />
          <Route path="/student/dashboard" element={<p>Student dashboard destination</p>} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('University Email Address'), {
      target: { value: 'admin@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'test-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Admin dashboard destination')).toBeInTheDocument();
    expect(screen.queryByText('Student dashboard destination')).not.toBeInTheDocument();
  });

  it('submits edited profile data from the header save button', async () => {
    render(
      <MemoryRouter>
        <StudentProfileEditor />
      </MemoryRouter>
    );

    const firstName = await screen.findByDisplayValue('Ada');
    fireEvent.change(firstName, { target: { value: 'Augusta' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Save All Changes' })[0]);

    await waitFor(() => {
      expect(mocks.updateStudent).toHaveBeenCalledWith(
        'student-123',
        expect.objectContaining({ first_name: 'Augusta' })
      );
    });
    expect(await screen.findByText(/Profile updated successfully/i)).toBeInTheDocument();
  });

  it('gives every profile editor control an accessible name, including modal fields', async () => {
    render(
      <MemoryRouter>
        <StudentProfileEditor />
      </MemoryRouter>
    );

    await screen.findByDisplayValue('Ada');
    for (const name of [
      'First Name',
      'Last Name',
      'Department',
      'Degree Level',
      'Availability Status',
      'GPA / Standing (optional)',
      'Expected Graduation Year',
      'Statement of Purpose & Research Goals',
      'Supplementary Academic Bio',
    ]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole('button', { name: 'Add Project' }));
    for (const name of [
      'Project Title',
      'Your Role',
      'Description',
      'Repository or Project URL (optional)',
    ]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Skill' }));
    for (const name of [
      'Select Topic / Skill',
      'Proficiency Level (1-5)',
      'Interest Level (1-5)',
    ]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }
  });

  it('provides a keyboard-focusable, named faculty profile link', async () => {
    render(
      <MemoryRouter>
        <FacultyDirectory />
      </MemoryRouter>
    );

    const profileLink = await screen.findByRole('link', {
      name: 'View Grace Hopper profile',
    });
    profileLink.focus();
    expect(profileLink).toHaveFocus();
    expect(profileLink).toHaveAttribute('href', '/faculty/faculty-123');
    expect(profileLink.closest('[role="link"]')).toBeNull();
  });

  it('reports an unavailable admin summary without replacing successful sections', async () => {
    mocks.getSummary.mockRejectedValue(new Error('summary unavailable'));
    mocks.getJobs.mockResolvedValue([]);

    render(<AdminDashboard />);

    expect(
      await screen.findByText(/Could not load scholarly summary: summary unavailable/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText('Unavailable')).toHaveLength(2);
    const jobsCard = screen.getByText('Import Jobs Audit').parentElement?.parentElement;
    expect(jobsCard).not.toBeNull();
    expect(within(jobsCard as HTMLElement).getByText('0')).toBeInTheDocument();
  });

  it('associates accessible names with admin dashboard form controls', async () => {
    render(<AdminDashboard />);

    for (const name of ['Students', 'Faculty', 'Publications', 'Random Seed']) {
      expect(screen.getByRole('spinbutton', { name })).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole('button', { name: /Real Research Ingestion/i }));
    expect(
      screen.getByRole('textbox', { name: 'Research Topic / Paper Title' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('textbox', { name: 'Institution ROR Filter (Optional)' })
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Institutional CSV Roster/i }));
    expect(
      screen.getByRole('textbox', { name: 'Institutional faculty roster CSV' })
    ).toBeInTheDocument();
  });

  it('displays the backend embedding total instead of an unrelated zero fallback', async () => {
    mocks.getStats.mockResolvedValue({
      total_embeddings: 42,
      by_entity_type: { STUDENT: 42 },
      by_model: [],
      active_model: 'test-model',
      active_dimension: 384,
    });

    render(<AdminDashboard />);

    expect(await screen.findByText('42')).toBeInTheDocument();
  });

  it('does not present fabricated benchmark metrics when the backend has no results', async () => {
    mocks.unused.mockResolvedValueOnce({
      benchmark_suite: 'standard_eval_v1',
      status: 'NO_JUDGMENTS_FOUND',
      message: 'No relevance judgments found for this suite.',
    });

    render(<AdminDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Run Benchmark Evaluation/i }));

    expect(
      await screen.findByText('No relevance judgments found for this suite.')
    ).toBeInTheDocument();
    expect(screen.queryByText('0.88')).not.toBeInTheDocument();
    expect(screen.queryByText('0.84')).not.toBeInTheDocument();
  });

  it('uses the faculty verification API pagination controls', async () => {
    const facultyItem = {
      id: 'faculty-queue-1',
      first_name: 'Taylor',
      last_name: 'Researcher',
      department: 'Computer Science',
      title_rank: 'ASSISTANT_PROFESSOR',
      lab_name: null,
      accepting_students: true,
      is_synthetic: false,
      verification_status: 'PENDING_REVIEW',
      openalex_id: null,
      institution_name: null,
      verification_notes: null,
      verified_at: null,
    };
    mocks.listVerificationFaculty
      .mockResolvedValueOnce({ items: [facultyItem], total: 21, page: 1, per_page: 20 })
      .mockResolvedValueOnce({ items: [facultyItem], total: 21, page: 2, per_page: 20 });

    render(<AdminDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Faculty Verification Review/i }));

    expect(await screen.findByText('Page 1 of 2 · 21 faculty')).toBeInTheDocument();
    expect(mocks.listVerificationFaculty).toHaveBeenLastCalledWith({
      status_filter: undefined,
      page: 1,
      per_page: 20,
    });

    fireEvent.click(screen.getByRole('button', { name: 'Next faculty verification page' }));

    await waitFor(() => {
      expect(mocks.listVerificationFaculty).toHaveBeenLastCalledWith({
        status_filter: undefined,
        page: 2,
        per_page: 20,
      });
    });
  });

  it('associates labels with faculty verification editor controls', async () => {
    mocks.listVerificationFaculty.mockResolvedValue({
      items: [{
        id: 'faculty-edit-1',
        first_name: 'Taylor',
        last_name: 'Researcher',
        department: 'Computer Science',
        title_rank: 'ASSISTANT_PROFESSOR',
        lab_name: null,
        accepting_students: true,
        is_synthetic: false,
        verification_status: 'PENDING_REVIEW',
        openalex_id: null,
        institution_name: null,
        verification_notes: null,
        verified_at: null,
      }],
      total: 1,
      page: 1,
      per_page: 20,
    });

    render(<AdminDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Faculty Verification Review/i }));
    await screen.findByText(/Taylor Researcher/);
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));

    for (const name of [
      'Verification Status',
      'Department',
      'Title Rank',
      'Verification Notes & Decision Rationale',
    ]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }
  });

  it('shows retry failure feedback instead of leaving a rejected request unhandled', async () => {
    mocks.getJobs.mockResolvedValue([{
      id: 'failed-job-1',
      data_source_id: 'source-1',
      status: 'FAILED',
      records_processed: 0,
      records_created: 0,
      records_updated: 0,
      error_log: [],
      started_at: null,
    }]);
    mocks.retryJob.mockRejectedValue(
      new Error('Import job retries are not implemented; no job state was changed.')
    );

    render(<AdminDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Import Jobs Audit Log/i }));
    fireEvent.click(await screen.findByRole('button', { name: 'Retry' }));

    expect(
      await screen.findByText(
        'Import job retries are not implemented; no job state was changed.'
      )
    ).toBeInTheDocument();
    expect(mocks.retryJob).toHaveBeenCalledWith('failed-job-1');
  });

  it('shows an explicit error when the faculty verification queue fails', async () => {
    mocks.listVerificationFaculty.mockRejectedValue(new Error('verification unavailable'));

    render(<AdminDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /Faculty Verification Review/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /Faculty verification records are unavailable: verification unavailable/i
    );
  });
});
