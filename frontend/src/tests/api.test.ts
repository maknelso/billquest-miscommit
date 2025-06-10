import { describe, it, expect } from 'vitest';

describe('API Utilities', () => {
  it('should format query parameters correctly', () => {
    const params = { queryType: 'account', accountId: '123456789012' };
    const queryString = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      queryString.append(key, value.toString());
    });
    
    expect(queryString.toString()).toBe('queryType=account&accountId=123456789012');
  });
  
  it('should handle empty parameters', () => {
    const params = {};
    const queryString = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      queryString.append(key, value.toString());
    });
    
    expect(queryString.toString()).toBe('');
  });
});