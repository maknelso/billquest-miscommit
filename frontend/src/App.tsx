import { useState, type FormEvent, useEffect } from 'react';
import './App.css'; // Keep this import if you still have an App.css file, otherwise remove it
// Authentication imports commented out for development
// import { getCurrentUser } from './aws/auth';
// import { useNavigate } from 'react-router-dom';
import Header from './components/Header';
import './components/Header.css';
import DataVisualization from './components/DataVisualization';
import ApiDebugger from './components/ApiDebugger';
import './components/api-debugger.css';

function App() {
  // Authentication state commented out for development
  // const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  // const [isLoading, setIsLoading] = useState<boolean>(true);
  const [payerAccountId, setPayerAccountId] = useState<string>('');
  const [billPeriodStartDate, setBillPeriodStartDate] = useState<string>('');
  const [invoiceId, setInvoiceId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<string | null>(null); // New state for API response
  // Initialize with empty array - will be populated from API response
  const [responseData, setResponseData] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  // const navigate = useNavigate();
  
  // State for available invoice IDs from API
  const [availableInvoiceIds, setAvailableInvoiceIds] = useState<string[]>([]);
  const [isLoadingInvoiceIds, setIsLoadingInvoiceIds] = useState<boolean>(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setApiResponse(null); // Clear previous response on new submission
    setResponseData([]); // Clear previous visualization data
    setIsSubmitting(true); // Disable the button and change text

    // Basic validation for payerAccountId
    if (!payerAccountId.trim()) {
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
    
    // Debug information
    console.log('API Request Details:');
    console.log('- URL:', apiUrl);
    console.log('- Query Parameters:', Object.fromEntries(queryParams.entries()));
    console.log('- Payer Account ID:', payerAccountId);
    console.log('- Bill Period Start Date:', billPeriodStartDate || 'Not provided');
    console.log('- Invoice ID:', invoiceId || 'Not provided');

    try {
      // Make a GET request to the API Gateway
      console.log('Sending API request...');
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          // You might need an API Key here if your API Gateway uses one
          // 'X-Api-Key': 'YOUR_API_KEY_HERE',
        },
      });

      console.log('API Response Status:', response.status, response.statusText);
      console.log('API Response Headers:', Object.fromEntries([...response.headers.entries()]));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`API request failed with status ${response.status}: ${errorText || response.statusText}`);
      }

      const responseText = await response.text();
      console.log('API Raw Response:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Error parsing JSON response:', parseError);
        throw new Error('Invalid JSON response from API');
      }
      console.log('Parsed Response from API:', data);
      console.log('Response Structure:', {
        hasItems: Boolean(data?.items),
        itemsIsArray: Array.isArray(data?.items),
        itemsLength: data?.items?.length || 0
      });
      
      if (data?.items?.length === 0) {
        console.warn('API returned empty items array. Possible issues:');
        console.warn('1. No data exists for the provided parameters');
        console.warn('2. Query parameters might be incorrect');
        console.warn('3. DynamoDB query might not be finding matching records');
        alert('No data found for the provided parameters. Please try different search criteria or use the API Debugger to check available data.');
      }
      
      setApiResponse(JSON.stringify(data, null, 2)); // Store pretty-printed JSON response
      
      // Store the items array for visualization
      if (data && data.items && Array.isArray(data.items)) {
        setResponseData(data.items);
      } else {
        // If API returns empty or invalid data, set empty array
        console.log('API returned empty or invalid results');
        setResponseData([]);
      }
      
      alert('Request submitted successfully!'); // Good user feedback

    } catch (err) {
      console.error('Error submitting form:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(`Failed to submit the form: ${errorMessage}`);
      setApiResponse(null); // Clear response on error
      setResponseData([]); // Clear visualization data
      alert(`Failed to submit the form: ${errorMessage}`);
    } finally {
      setIsSubmitting(false); // Re-enable the button regardless of success or failure
    }
  };
  
  // Function to fetch available invoice IDs when payer account ID changes
  const fetchInvoiceIds = async (accountId: string) => {
    if (!accountId.trim()) return;
    
    console.log(`Fetching invoice IDs for account: ${accountId}`);
    setIsLoadingInvoiceIds(true);
    setAvailableInvoiceIds([]);
    
    const queryParams = new URLSearchParams();
    queryParams.append('queryType', 'getInvoiceIds');
    queryParams.append('accountId', accountId);
    
    const apiUrl = `https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query?${queryParams.toString()}`;
    console.log(`API URL: ${apiUrl}`);
    
    try {
      const response = await fetch(apiUrl);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API error response: ${errorText}`);
        throw new Error(`Failed to fetch invoice IDs: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Invoice IDs API response:', data);
      
      if (data && data.invoiceIds && Array.isArray(data.invoiceIds)) {
        console.log(`Found ${data.invoiceIds.length} invoice IDs`);
        setAvailableInvoiceIds(data.invoiceIds);
      } else {
        console.warn('No invoice IDs found in response or invalid format:', data);
      }
    } catch (err) {
      console.error('Error fetching invoice IDs:', err);
      // Don't show an alert for this background operation
    } finally {
      setIsLoadingInvoiceIds(false);
    }
  };
  
  // Call fetchInvoiceIds when payerAccountId changes
  useEffect(() => {
    console.log(`payerAccountId changed to: "${payerAccountId}"`);
    if (payerAccountId.trim()) {
      console.log("Calling fetchInvoiceIds...");
      fetchInvoiceIds(payerAccountId);
    } else {
      console.log("Clearing availableInvoiceIds");
      setAvailableInvoiceIds([]);
    }
  }, [payerAccountId]);

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

  // Authentication check commented out for development
  /*
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
  */

  return (
    <div className="app-container">
      <Header />
      
      {/* Three-column layout */}
      <div className="content-container">
        {/* Left panel - Bill Information Request Form */}
        <div className="left-panel">
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
              {isLoadingInvoiceIds ? (
                <div className="loading-spinner">Loading invoice IDs...</div>
              ) : availableInvoiceIds.length > 0 ? (
                <>
                  <select
                    id="invoiceId"
                    value={invoiceId}
                    onChange={(e) => setInvoiceId(e.target.value)}
                  >
                    <option value="">Select an Invoice ID</option>
                    {availableInvoiceIds.map(id => (
                      <option key={id} value={id}>{id}</option>
                    ))}
                  </select>
                  <div className="debug-info">Found {availableInvoiceIds.length} invoice IDs</div>
                </>
              ) : (
                <>
                  <input
                    type="text"
                    id="invoiceId"
                    value={invoiceId}
                    onChange={(e) => setInvoiceId(e.target.value)}
                    placeholder={payerAccountId ? "No invoice IDs found" : "Enter Payer Account ID first"}
                    disabled={!payerAccountId.trim()}
                  />
                  {payerAccountId.trim() && !isLoadingInvoiceIds && (
                    <div className="debug-info">No invoice IDs found for this account</div>
                  )}
                </>
              )}
            </div>

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          </form>
        </div>
        
        {/* Center panel - Data Visualization */}
        <div className="center-panel">
          {apiResponse ? (
            <div className="visualization-section">
              <h3>Data Visualization</h3>
              <DataVisualization data={responseData} />
            </div>
          ) : (
            <div className="visualization-section">
              <h3>Data Visualization</h3>
              <p>Submit a request to see visualization</p>
            </div>
          )}
        </div>
        
        {/* Right panel - Download CSV */}
        <div className="right-panel">
          <div className="right-panel-container">
            <div className="right-panel-title">Actions</div>
            <button 
              onClick={handleDownloadCSV} 
              className="download-csv-button"
              disabled={!apiResponse}
            >
              Download CSV
            </button>
          </div>
        </div>
      </div>
      
      {/* API Response section (below the three columns) */}
      {apiResponse && (
        <div className="api-response-container">
          <div className="response-header">
            <h3>API Response:</h3>
          </div>
          <textarea
            readOnly
            value={apiResponse}
            rows={5} // Reduced rows since we have more content above
            cols={50}
            style={{ width: '100%', resize: 'vertical' }}
          ></textarea>
        </div>
      )}
      
      {/* API Debugger (only shown when there's a response) */}
      {apiResponse && (
        <ApiDebugger apiUrl="https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query" />
      )}
    </div>
  );
}

export default App;