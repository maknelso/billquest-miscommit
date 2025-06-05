import { fetchAuthSession } from 'aws-amplify/auth';
import { 
  QueryParams, 
  UserAccountsParams, 
  QueryDataResponse, 
  UserAccountsResponse,
  ApiErrorResponse
} from '../types/api';

// API endpoints
const QUERY_API_URL = 'https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query';
const USER_ACCOUNTS_API_URL = 'https://saplj0po57.execute-api.us-east-1.amazonaws.com/prod/user-accounts';

// Helper function to get auth token
async function getAuthToken(): Promise<string | undefined> {
  try {
    const { tokens } = await fetchAuthSession();
    return tokens?.idToken?.toString();
  } catch (error) {
    console.error('Error getting auth token:', error);
    return undefined;
  }
}

// Helper function to handle API errors
function handleApiError(error: unknown): never {
  if (error instanceof Response) {
    throw new Error(`API request failed with status ${error.status}: ${error.statusText}`);
  } else if (error instanceof Error) {
    throw error;
  } else {
    throw new Error(String(error));
  }
}

// Query data API
export async function queryData(params: QueryParams): Promise<QueryDataResponse> {
  try {
    const queryParams = new URLSearchParams();
    
    // Add all params to query string
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${QUERY_API_URL}?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API request failed with status ${response.status}: ${errorText || response.statusText}`);
    }
    
    return await response.json() as QueryDataResponse;
  } catch (error) {
    return handleApiError(error);
  }
}

// Download CSV data
export async function downloadCsv(params: QueryParams): Promise<Blob> {
  try {
    const queryParams = new URLSearchParams();
    
    // Add all params to query string
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });
    
    // Always set format to csv
    queryParams.append('format', 'csv');
    
    const response = await fetch(`${QUERY_API_URL}?${queryParams.toString()}`, {
      method: 'GET'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to download CSV: ${response.statusText}`);
    }
    
    return await response.blob();
  } catch (error) {
    return handleApiError(error);
  }
}

// Get user accounts API
export async function getUserAccounts(params: UserAccountsParams): Promise<UserAccountsResponse> {
  try {
    const idToken = await getAuthToken();
    
    const queryParams = new URLSearchParams();
    queryParams.append('email', params.email);
    
    const response = await fetch(`${USER_ACCOUNTS_API_URL}?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': idToken ? `Bearer ${idToken}` : '',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch user accounts: ${response.status} ${errorText || response.statusText}`);
    }
    
    return await response.json() as UserAccountsResponse;
  } catch (error) {
    return handleApiError(error);
  }
}