import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import App from '../../App';

// Skip tests if not in test environment
const runTests = process.env.TEST_ENV === 'integration';

// Mock the auth module to simulate authenticated state
vi.mock('../../aws/auth', () => ({
  isAuthenticated: vi.fn().mockResolvedValue(true),
  getCurrentUser: vi.fn().mockResolvedValue({ username: 'testuser', email: 'test@example.com' }),
  signIn: vi.fn().mockResolvedValue({ isSignedIn: true, idToken: 'mock-token' }),
  signOut: vi.fn().mockResolvedValue(undefined)
}));

// Mock API calls to return test data
vi.mock('../../services/api', () => ({
  queryData: vi.fn().mockResolvedValue({
    items: [
      {
        payer_account_id: '123456789012',
        invoice_id: 'INV123',
        product_code: 'EC2',
        bill_period_start_date: '2023-01-01',
        cost_before_tax: '100.50'
      }
    ],
    count: 1
  }),
  getUserAccounts: vi.fn().mockResolvedValue({
    email: 'test@example.com',
    payer_account_ids: ['123456789012', '210987654321']
  })
}));

(runTests ? describe : describe.skip)('Component Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the app', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    
    // Wait for the app to load and check for the header
    await waitFor(() => {
      expect(screen.getByText('BillQuest')).toBeInTheDocument();
    });
    
    // Check for the form
    expect(screen.getByText('Bill Information Request')).toBeInTheDocument();
  });

  it('should handle form interactions', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    
    // Wait for the app to load
    await waitFor(() => {
      expect(screen.getByText('BillQuest')).toBeInTheDocument();
    });
    
    // Find form inputs
    const dateInput = screen.getByLabelText(/Bill Period Start Date/i);
    const invoiceInput = screen.getByLabelText(/Invoice ID/i);
    
    // Fill out the form
    fireEvent.change(dateInput, { target: { value: '2023-01' } });
    fireEvent.change(invoiceInput, { target: { value: 'INV123' } });
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Just verify the form submission doesn't crash
    expect(screen.getByText('BillQuest')).toBeInTheDocument();
  });
});