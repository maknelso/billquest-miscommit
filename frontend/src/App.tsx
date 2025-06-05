import { useState, type FormEvent, useEffect } from 'react';
import './App.css'; // Keep this import if you still have an App.css file, otherwise remove it
import { getCurrentUser } from './aws/auth';
import { fetchAuthSession } from 'aws-amplify/auth';
import { useNavigate } from 'react-router-dom';
import Header from './components/Header';
import './components/Header.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // We don't need a separate userEmail state since we're using it only for fetching accounts
  const [payerAccountId, setPayerAccountId] = useState<string[]>([]);
  const [availableAccounts, setAvailableAccounts] = useState<string[]>([]);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [billPeriodStartDate, setBillPeriodStartDate] = useState<string>('');
  const [invoiceId, setInvoiceId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<string | null>(null); // New state for API response
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setApiResponse(null); // Clear previous response on new submission
    setIsSubmitting(true); // Disable the button and change text

    // Basic validation for payerAccountId
    if (payerAccountId.length === 0) {
      alert('Payer Account ID is required!');
      setIsSubmitting(false); // Re-enable the button
      return;
    }

    // Validation for at least one of the date or invoice ID
    if (!billPeriodStartDate.trim() && !invoiceId.trim()) {
      alert('Please provide either a Bill Period Start Date OR an Invoice ID.');
      setIsSubmitting(false); // Re-enable the button
      return;
    }

    const queryParams = new URLSearchParams();
    // Correctly map your form inputs to the Lambda's expected query parameters
    queryParams.append('queryType', 'account'); // Assuming 'account' is the queryType for this form
    queryParams.append('accountId', payerAccountId.join(',')); // Join multiple account IDs with commas

    // Only append one of the date or invoice ID, based on which one is provided
    if (billPeriodStartDate.trim()) {
      // Assuming your Lambda expects 'billPeriodStartDate' as a parameter
      queryParams.append('billPeriodStartDate', billPeriodStartDate);
    } else if (invoiceId.trim()) {
      // Assuming your Lambda expects 'invoiceId' as a parameter
      queryParams.append('invoiceId', invoiceId);
    }

    // Use the confirmed working API Gateway URL
    const apiUrl = `https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query?${queryParams.toString()}`;

    try {
      // Make a GET request to the API Gateway
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          // You might need an API Key here if your API Gateway uses one
          // 'X-Api-Key': 'YOUR_API_KEY_HERE',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed with status ${response.status}: ${errorText || response.statusText}`);
      }

      const data = await response.json();
      console.log('Response from API:', data);
      setApiResponse(JSON.stringify(data, null, 2)); // Store pretty-printed JSON response
      alert('Request submitted successfully!'); // Good user feedback

    } catch (err) {
      console.error('Error submitting form:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(`Failed to submit the form: ${errorMessage}`);
      setApiResponse(null); // Clear response on error
      alert(`Failed to submit the form: ${errorMessage}`);
    } finally {
      setIsSubmitting(false); // Re-enable the button regardless of success or failure
    }
  };
  
  const handleDownloadCSV = async () => {
    if (payerAccountId.length === 0) {
      alert('Please submit a query first before downloading CSV');
      return;
    }
    
    const queryParams = new URLSearchParams();
    queryParams.append('queryType', 'account');
    queryParams.append('accountId', payerAccountId.join(','));
    queryParams.append('format', 'csv'); // Request CSV format
    
    if (billPeriodStartDate.trim()) {
      queryParams.append('billPeriodStartDate', billPeriodStartDate);
    } else if (invoiceId.trim()) {
      queryParams.append('invoiceId', invoiceId);
    }
    
    const apiUrl = `https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query?${queryParams.toString()}`;
    
    try {
      const response = await fetch(apiUrl, {
        method: 'GET',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to download CSV: ${response.statusText}`);
      }
      
      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a download link and trigger the download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'billing_data.csv';
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      console.error('Error downloading CSV:', err);
      alert(`Failed to download CSV: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Fetch user accounts from the API
  const fetchUserAccounts = async (email: string) => {
    if (!email) return;
    
    console.log('Attempting to fetch accounts for email:', email);
    setIsLoadingAccounts(true);
    try {
      // Use the actual API endpoint from CloudFormation outputs
      const apiUrl = `https://saplj0po57.execute-api.us-east-1.amazonaws.com/prod/user-accounts?email=${encodeURIComponent(email)}`;
      console.log('API URL:', apiUrl);
      
      // Get the current user's session for authentication
      // In Amplify v6, we need to use a different approach to get the token
      const { tokens } = await fetchAuthSession();
      const idToken = tokens?.idToken?.toString();
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': idToken ? `Bearer ${idToken}` : ''
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        throw new Error(`Failed to fetch user accounts: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API response data:', data);
      if (data.payer_account_ids && Array.isArray(data.payer_account_ids)) {
        // Sort accounts in descending order
        const sortedAccounts = [...data.payer_account_ids].sort((a, b) => b.localeCompare(a));
        setAvailableAccounts(sortedAccounts);
        
        // If accounts are available, set the first one as default
        if (sortedAccounts.length > 0) {
          setPayerAccountId([sortedAccounts[0]]);
        }
      } else {
        setAvailableAccounts([]);
      }
    } catch (err) {
      console.error('Error fetching user accounts:', err);
      // Show more detailed error in console
      if (err instanceof Error) {
        console.error('Error details:', err.message, err.stack);
      }
      setError(`Failed to load your account information. Please try again later.`);
    } finally {
      setIsLoadingAccounts(false);
    }
  };

  useEffect(() => {
    async function checkAuthStatus() {
      try {
        const user = await getCurrentUser();
        if (user) {
          setIsAuthenticated(true);
          
          // Get user email from Cognito
          // Use username + domain to form complete email address
          const username = user.username || '';
          const email = username.includes('@') ? username : `${username}@amazon.com`;
          console.log('User email captured:', email);
          console.log('Full user object:', user);
          
          // Fetch user accounts once we have the email
          if (email) {
            fetchUserAccounts(email);
          }
        } else {
          // Redirect to login if not authenticated
          navigate('/login');
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        navigate('/login');
      } finally {
        setIsLoading(false);
      }
    }
    
    checkAuthStatus();
  }, [navigate]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="app-container">
      <Header />
      <form onSubmit={handleSubmit} className="billing-form">
        <h2>Bill Information Request</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <div className="form-group">
          <label htmlFor="payerAccountId">Payer Account ID: (required)</label>
          {isLoadingAccounts ? (
            <div className="loading-accounts">Loading your accounts...</div>
          ) : availableAccounts.length > 0 ? (
            <div className="account-select-container">
              <input
                type="text"
                placeholder="Search accounts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="account-search"
              />
              <div className="account-options">
                {availableAccounts
                  .filter(account => account.toLowerCase().includes(searchTerm.toLowerCase()))
                  .map((account) => (
                    <div 
                      key={account} 
                      className={`account-option ${payerAccountId.includes(account) ? 'selected' : ''}`}
                      onClick={() => {
                        if (payerAccountId.includes(account)) {
                          setPayerAccountId(payerAccountId.filter(id => id !== account));
                        } else {
                          setPayerAccountId([...payerAccountId, account]);
                        }
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={payerAccountId.includes(account)}
                        onChange={() => {}} // Handled by the onClick of the parent div
                      />
                      <span>{account}</span>
                    </div>
                  ))}
              </div>
              {payerAccountId.length > 0 && (
                <div className="selected-accounts">
                  <div className="selected-count">{payerAccountId.length} account(s) selected</div>
                </div>
              )}
            </div>
          ) : (
            <div className="no-accounts">
              No accounts found for your email. Please contact support.
            </div>
          )}
        </div>

        <p className="choose-one-text">Choose at least ONE of the below:</p>

        <div className="form-group">
          <label htmlFor="billPeriodStartDate">Bill Period Start Date:</label>
          <input
            type="text"
            id="billPeriodStartDate"
            value={billPeriodStartDate}
            onChange={(e) => setBillPeriodStartDate(e.target.value)}
            placeholder="e.g. 2023-01"
          />
        </div>

        <div className="form-group">
          <label htmlFor="invoiceId">Invoice ID:</label>
          <input
            type="text"
            id="invoiceId"
            value={invoiceId}
            onChange={(e) => setInvoiceId(e.target.value)}
            placeholder="e.g. EUINFR25-123456"
          />
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit'}
        </button>
      </form>

      {/* New section to display API response */}
      {apiResponse && (
        <div className="api-response-container">
          <div className="response-header">
            <h3>API Response:</h3>
            <button 
              onClick={handleDownloadCSV} 
              className="download-csv-button"
            >
              Download CSV
            </button>
          </div>
          <textarea
            readOnly
            value={apiResponse}
            rows={10} // Adjust rows as needed
            cols={50} // Adjust cols as needed
            style={{ width: '100%', resize: 'vertical' }}
          ></textarea>
        </div>
      )}
    </div>
  );
}

export default App;