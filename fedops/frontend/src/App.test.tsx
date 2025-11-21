import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the header', () => {
    render(<App />);
    expect(screen.getByText('FedOps Opportunities')).toBeInTheDocument();
  });

  it('renders the search form', () => {
    render(<App />);
    expect(screen.getByLabelText(/Posted From/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Posted To/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Limit/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search/i })).toBeInTheDocument();
  });
});
