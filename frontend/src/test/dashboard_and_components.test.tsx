import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Navbar } from '../components/layout/Navbar';
import { AuthProvider } from '../context/AuthContext';

describe('Card Component Suite', () => {
  it('renders card with children content and styling', () => {
    render(
      <Card hoverEffect glass data-testid="test-card">
        <h3>Research Profile</h3>
        <p>Active publications and skills</p>
      </Card>
    );

    expect(screen.getByText('Research Profile')).toBeInTheDocument();
    expect(screen.getByText('Active publications and skills')).toBeInTheDocument();
  });
});

describe('EmptyState Component', () => {
  it('renders title, description and action button', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="No Recommendations Generated"
        description="Complete your student profile with at least one skill to generate recommendations."
        actionText="Update Profile"
        onAction={handleAction}
      />
    );

    expect(screen.getByText('No Recommendations Generated')).toBeInTheDocument();
    expect(
      screen.getByText(/Complete your student profile with at least one skill/i)
    ).toBeInTheDocument();

    const actionBtn = screen.getByRole('button', { name: /Update Profile/i });
    expect(actionBtn).toBeInTheDocument();
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });
});

describe('Modal Component', () => {
  it('renders modal content when isOpen is true', () => {
    const handleClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Weight Configuration">
        <p>Custom weights for recommendation ranking</p>
      </Modal>
    );

    expect(screen.getByText('Weight Configuration')).toBeInTheDocument();
    expect(screen.getByText('Custom weights for recommendation ranking')).toBeInTheDocument();
  });

  it('does not render modal content when isOpen is false', () => {
    const handleClose = vi.fn();
    render(
      <Modal isOpen={false} onClose={handleClose} title="Hidden Modal">
        <p>Should not be in document</p>
      </Modal>
    );

    expect(screen.queryByText('Hidden Modal')).not.toBeInTheDocument();
  });

  it('names the dialog, traps focus, closes with Escape, and restores focus', async () => {
    const handleClose = vi.fn();
    const renderModal = (isOpen: boolean) => (
      <>
        <button type="button" data-testid="modal-trigger">Open modal</button>
        <Modal isOpen={isOpen} onClose={handleClose} title="Accessible dialog">
          <button type="button">First action</button>
          <button type="button">Last action</button>
        </Modal>
      </>
    );
    const { rerender } = render(renderModal(false));
    const trigger = screen.getByTestId('modal-trigger');
    trigger.focus();
    rerender(renderModal(true));

    const dialog = screen.getByRole('dialog', { name: 'Accessible dialog' });
    await waitFor(() => expect(dialog).toHaveFocus());

    fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
    expect(screen.getByRole('button', { name: 'Last action' })).toHaveFocus();
    fireEvent.keyDown(window, { key: 'Tab' });
    expect(screen.getByRole('button', { name: 'Close dialog' })).toHaveFocus();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
    rerender(renderModal(false));
    expect(trigger).toHaveFocus();
  });

  it('constrains dialog height and keeps the title available while content scrolls', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Scrollable evidence">
        <div>Long evidence content</div>
      </Modal>
    );

    const dialog = screen.getByRole('dialog', { name: 'Scrollable evidence' });
    expect(dialog.className).toContain('max-h-[calc(100dvh-4rem)]');
    expect(dialog.className).toContain('overflow-y-auto');
    expect(dialog.querySelector('h2')?.parentElement?.className).toContain('sticky');
  });
});

describe('LoadingSpinner Component', () => {
  it('renders accessible loading text when provided', () => {
    render(<LoadingSpinner message="Calculating embedding similarities..." />);
    expect(screen.getByText('Calculating embedding similarities...')).toBeInTheDocument();
  });
});

describe('Navbar Layout Component', () => {
  it('renders public navigation links and brand name', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Navbar />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Researchers')).toBeInTheDocument();
    expect(screen.queryByText('Demo Student')).not.toBeInTheDocument();
    expect(screen.queryByText('Demo Admin')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('keeps desktop navigation at large widths and exposes the mobile menu below them', () => {
    const { container } = render(
      <MemoryRouter>
        <AuthProvider>
          <Navbar />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(container.querySelector('nav')?.className).toContain('hidden lg:flex');
    expect(screen.getByRole('button', { name: 'Toggle mobile menu' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Toggle mobile menu' }));
    expect(screen.getByText('Researchers Directory')).toBeInTheDocument();
  });
});
