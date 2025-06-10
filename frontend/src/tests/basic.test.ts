import { describe, it, expect } from 'vitest';

// Simple test that will pass
describe('Basic Tests', () => {
  it('should pass a simple test', () => {
    expect(1 + 1).toBe(2);
  });
  
  it('should handle string operations', () => {
    expect('hello ' + 'world').toBe('hello world');
  });
});