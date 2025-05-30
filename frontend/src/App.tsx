import { useState, type FormEvent, useEffect } from 'react';
import './App.css'; // Keep this import if you still have an App.css file, otherwise remove it
import { getCurrentUser } from './aws/auth';
import { useNavigate } from 'react-router-dom';
import Header from './components/Header';
import './components/Header.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [payerAccountId, setPayerAccountId] = useState<string>('');
  const [billPeriodStartDate, setBillPeriodStartDate] = useState<string>('');
  const [invoiceId, setInvoiceId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<string | null>(null); // New state for API response
  const navigate = useNavigate();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setApiResponse(null); // Clear previous response on new submission

    // Basic validation for payerAccountId
    if (!payerAccountId.trim()) {
      alert('Payer Account ID is required!');
      return;
    }

    // Validation for at least one of the date or invoice ID
    if (!billPeriodStartDate.trim() && !invoiceId.trim()) {
      alert('Please provide either a Bill Period Start Date OR an Invoice ID.');
      return;
    }

    const queryParams = new URLSearchParams();
    // Correctly map your form inputs to the Lambda's expected query parameters
    queryParams.append('queryType', 'account'); // Assuming 'account' is the queryType for this form
    queryParams.append('accountId', payerAccountId); // Use payerAccountId as accountId for Lambda

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
    }
  };
  
  const handleDownloadCSV = async () => {
    if (!payerAccountId.trim()) {
      alert('Please submit a query first before downloading CSV');
      return;
    }
    
    const queryParams = new URLSearchParams();
    queryParams.append('queryType', 'account');
    queryParams.append('accountId', payerAccountId);
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

  useEffect(() => {
    async function checkAuthStatus() {
      try {
        const user = await getCurrentUser();
        if (user) {
          setIsAuthenticated(true);
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
          <input
            type="text"
            id="payerAccountId"
            value={payerAccountId}
            onChange={(e) => setPayerAccountId(e.target.value)}
            required
          />
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

        <button type="submit">Submit</button>
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