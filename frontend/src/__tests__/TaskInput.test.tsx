import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskInput } from '../components/TaskInput';
import React from 'react';

describe('TaskInput Component', () => {
  it('renders input area and submit button', () => {
    const mockSubmit = vi.fn();
    render(<TaskInput onSubmit={mockSubmit} isRunning={false} />);
    
    // Check if placeholder is displayed
    expect(screen.getByPlaceholderText(/Compare iPhone 16 prices/i)).toBeInTheDocument();
    
    // Check that button is rendered
    const button = screen.getByRole('button', { name: /Run Task/i });
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled(); // Disabled initially due to character count constraint
  });

  it('enables the submit button when valid text is typed', () => {
    const mockSubmit = vi.fn();
    render(<TaskInput onSubmit={mockSubmit} isRunning={false} />);
    
    const textarea = screen.getByPlaceholderText(/Compare iPhone 16 prices/i);
    const button = screen.getByRole('button', { name: /Run Task/i });
    
    // Type a short prompt (less than 10 characters)
    fireEvent.change(textarea, { target: { value: 'short' } });
    expect(button).toBeDisabled();

    // Type a valid prompt
    fireEvent.change(textarea, { target: { value: 'Compare flight prices from HYD to BLR under 5k' } });
    expect(button).toBeEnabled();
  });

  it('calls onSubmit with entered text when button clicked', () => {
    const mockSubmit = vi.fn();
    render(<TaskInput onSubmit={mockSubmit} isRunning={false} />);
    
    const textarea = screen.getByPlaceholderText(/Compare iPhone 16 prices/i);
    const button = screen.getByRole('button', { name: /Run Task/i });
    
    const promptText = 'Search for Python machine learning tutorials';
    fireEvent.change(textarea, { target: { value: promptText } });
    fireEvent.click(button);
    
    expect(mockSubmit).toHaveBeenCalledWith(promptText);
  });
});
