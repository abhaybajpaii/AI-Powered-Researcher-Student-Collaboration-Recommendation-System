import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { AuthProvider } from '../context/AuthContext';

describe('LandingPage Flow', () => {
  it('renders headline and multi-signal capabilities', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LandingPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/Match Students with Faculty Researchers/i)).toBeInTheDocument();
    expect(screen.getByText(/Through Evidence-Based AI/i)).toBeInTheDocument();
    expect(screen.getByText(/1. Research Intent/i)).toBeInTheDocument();
    expect(screen.getByText(/2. Project Experience/i)).toBeInTheDocument();
    expect(screen.getByText(/3. Publication Relevance/i)).toBeInTheDocument();
    expect(screen.getByText(/4. Skill Compatibility/i)).toBeInTheDocument();
  });
});
