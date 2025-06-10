import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Login from '../../pages/Login';

// Mock the auth module
vi.mock('../../aws/auth', () => ({
  signIn: vi.fn().mockResolvedValue({ isSignedIn: true })
}));

// Import the mocked module
import { signIn } from '../../aws/auth';

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    // Check that form elements are rendered
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });
  
  it('handles form submission', async () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    // Fill out the form
    fireEvent.change(screen.getByLabelText(/email/i), { 
      target: { value: 'test@example.com' } 
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), { 
      target: { value: 'password123' } 
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check that signIn was called with the correct arguments
    expect(signIn).toHaveBeenCalledWith('test@example.com', 'password123');
  });
  
  it('displays error message on failed login', async () => {
    // Override the mock to simulate a failed login
    (signIn as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Invalid credentials')
    );
    
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
    
    // Fill out the form
    fireEvent.change(screen.getByLabelText(/email/i), { 
      target: { value: 'wrong@example.com' } 
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), { 
      target: { value: 'wrongpassword' } 
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check that error message is displayed
    // Note: You may need to adjust this based on how your component displays errors
    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
  });
});