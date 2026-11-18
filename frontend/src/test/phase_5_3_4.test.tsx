import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { FacultyDirectory } from '../pages/FacultyDirectory';

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  listFaculty: vi.fn(),
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    isStudent: false,
    isAdmin: false,
    login: mocks.login,
    studentId: null,
    logout: vi.fn(),
  }),
}));

vi.mock('../api/faculty', () => ({
  facultyApi: { listFaculty: mocks.listFaculty },
}));

describe('Phase 5.3.4 demo login and directory accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.login.mockResolvedValue({ role: 'STUDENT' });
    mocks.listFaculty.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 12,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    });
  });

  it('sends the landing-page sign-in action to normal login, not a demo account', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<p>Normal sign-in page</p>} />
        </Routes>
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Demo accounts are not automatically provisioned/i)
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Sign In for Recommendations' }));

    expect(await screen.findByText('Normal sign-in page')).toBeInTheDocument();
    expect(mocks.login).not.toHaveBeenCalled();
  });

  it('preserves the admin destination from the landing-page admin sign-in action', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/admin" element={<p>Admin console</p>} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Admin Sign In' }));
    fireEvent.change(screen.getByLabelText('University Email Address'), {
      target: { value: 'admin-account@example.edu' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'user-supplied-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Admin console')).toBeInTheDocument();
  });

  it('removes demo autofill and explains account availability on login', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Demo accounts are not automatically provisioned/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/Quick Demo Autofill/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Student User' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Admin User' })).not.toBeInTheDocument();
  });

  it.each([
    ['/student/dashboard', 'Student dashboard'],
    ['/admin', 'Admin console'],
  ])('continues supporting normal sign-in to %s', async (destination, destinationText) => {
    render(
      <MemoryRouter
        initialEntries={[
          { pathname: '/login', state: { from: { pathname: destination } } },
        ]}
      >
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/student/dashboard" element={<p>Student dashboard</p>} />
          <Route path="/admin" element={<p>Admin console</p>} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('University Email Address'), {
      target: { value: `account-${destination === '/admin' ? 'admin' : 'student'}@example.edu` },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'user-supplied-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText(destinationText)).toBeInTheDocument();
    expect(mocks.login).toHaveBeenCalledWith(
      `account-${destination === '/admin' ? 'admin' : 'student'}@example.edu`,
      'user-supplied-password'
    );
  });

  it('displays clear feedback when normal login fails', async () => {
    mocks.login.mockRejectedValue(new Error('Incorrect email or password'));
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('University Email Address'), {
      target: { value: 'account@example.edu' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'invalid-user-supplied-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Incorrect email or password'
    );
  });

  it('shows fallback feedback for an unstructured login failure', async () => {
    mocks.login.mockRejectedValue(undefined);
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('University Email Address'), {
      target: { value: 'account@example.edu' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'user-supplied-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Login failed. Please check your credentials and try again.'
    );
  });

  it('gives the directory department combobox an accessible name', async () => {
    render(
      <MemoryRouter>
        <FacultyDirectory />
      </MemoryRouter>
    );

    const departmentFilter = await screen.findByRole('combobox', { name: 'Department' });
    expect(departmentFilter).toBeInTheDocument();
    await waitFor(() => expect(mocks.listFaculty).toHaveBeenCalled());
  });
});
