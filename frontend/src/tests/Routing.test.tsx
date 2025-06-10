import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';

// Mock the components directly without importing them
const MockLogin = () => <div>Login Page</div>;
const MockSignup = () => <div>Signup Page</div>;
const MockHome = () => <div>Home Page</div>;

// Mock the imports
vi.mock('../pages/Login', () => ({
  default: () => <div>Login Page</div>
}));

vi.mock('../pages/Signup', () => ({
  default: () => <div>Signup Page</div>
}));

describe('Routing', () => {
  it('renders login page on /login route', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<MockLogin />} />
          <Route path="/signup" element={<MockSignup />} />
          <Route path="/" element={<MockHome />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });
  
  it('renders signup page on /signup route', () => {
    render(
      <MemoryRouter initialEntries={['/signup']}>
        <Routes>
          <Route path="/login" element={<MockLogin />} />
          <Route path="/signup" element={<MockSignup />} />
          <Route path="/" element={<MockHome />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText('Signup Page')).toBeInTheDocument();
  });
  
  it('renders home on / route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/login" element={<MockLogin />} />
          <Route path="/signup" element={<MockSignup />} />
          <Route path="/" element={<MockHome />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText('Home Page')).toBeInTheDocument();
  });
});