import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../components/common/Button';
import { ScoreBar } from '../components/common/ScoreBar';
import { Badge, SyntheticBadge } from '../components/common/Badge';

describe('Common UI Components', () => {
  it('renders Button with text and triggers click event', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    const btn = screen.getByRole('button', { name: /click me/i });
    expect(btn).toBeInTheDocument();

    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders Button in loading state and disables it', () => {
    render(<Button isLoading>Submit</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders ScoreBar with percentage and label', () => {
    render(<ScoreBar label="Research Intent" score={0.85} weight={0.35} />);
    expect(screen.getByText('Research Intent')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('(w=35%)')).toBeInTheDocument();
  });

  it('renders Badge and SyntheticBadge correctly', () => {
    render(
      <div>
        <Badge variant="success">Active</Badge>
        <SyntheticBadge />
      </div>
    );

    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText(/synthetic demo/i)).toBeInTheDocument();
  });
});
