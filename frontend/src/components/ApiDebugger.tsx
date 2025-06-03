import React, { useState } from 'react';

interface ApiDebuggerProps {
  apiUrl: string;
}

const ApiDebugger: React.FC<ApiDebuggerProps> = ({ apiUrl }) => {
  const [debugResult, setDebugResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const runDiagnostics = async () => {
    setIsLoading(true);
    setDebugResult('Running diagnostics...\n');
    
    try {
      // Test 1: Basic connectivity
      setDebugResult(prev => prev + '\n1. Testing basic connectivity...');
      const baseUrl = apiUrl.split('?')[0];
      const response1 = await fetch(baseUrl);
      setDebugResult(prev => prev + `\n   Status: ${response1.status} ${response1.statusText}`);
      
      // Test 2: Check with minimal parameters
      setDebugResult(prev => prev + '\n\n2. Testing with minimal parameters...');
      const minimalUrl = `${baseUrl}?queryType=account&accountId=123456789012`;
      const response2 = await fetch(minimalUrl);
      const data2 = await response2.text();
      setDebugResult(prev => prev + `\n   Status: ${response2.status} ${response2.statusText}`);
      setDebugResult(prev => prev + `\n   Response: ${data2.substring(0, 100)}${data2.length > 100 ? '...' : ''}`);
      
      // Test 3: Check table scan to verify data exists
      setDebugResult(prev => prev + '\n\n3. Checking if DynamoDB table has data...');
      const scanUrl = `${baseUrl}?queryType=scan&limit=5`;
      const response3 = await fetch(scanUrl);
      const data3 = await response3.text();
      setDebugResult(prev => prev + `\n   Status: ${response3.status} ${response3.statusText}`);
      
      try {
        const jsonData = JSON.parse(data3);
        if (jsonData.count && jsonData.count > 0) {
          setDebugResult(prev => prev + `\n   Found ${jsonData.count} items in database`);
          if (jsonData.payer_account_ids && jsonData.payer_account_ids.length > 0) {
            setDebugResult(prev => prev + `\n   Available payer account IDs: ${jsonData.payer_account_ids.join(', ')}`);
            setDebugResult(prev => prev + `\n   ⚠️ Use one of these account IDs in your search form`);
          }
          if (jsonData.sample && jsonData.sample.length > 0) {
            setDebugResult(prev => prev + `\n   Sample product codes: ${jsonData.sample.map((item: any) => item.product_code || 'unknown').join(', ')}`);
          }
        } else {
          setDebugResult(prev => prev + `\n   ⚠️ No data found in database. Please check if data has been ingested.`);
          setDebugResult(prev => prev + `\n   The API cannot return visualization data if no records exist in the database.`);
        }
      } catch (e) {
        setDebugResult(prev => prev + `\n   Could not parse scan response: ${data3.substring(0, 100)}${data3.length > 100 ? '...' : ''}`);
      }
      
      setDebugResult(prev => prev + '\n\nDiagnostics complete. Check the console for more details.');
    } catch (error) {
      setDebugResult(prev => prev + `\n\nError during diagnostics: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="api-debugger">
      <h3>API Debugger</h3>
      <button 
        onClick={runDiagnostics} 
        disabled={isLoading}
        className="debug-button"
      >
        {isLoading ? 'Running...' : 'Run API Diagnostics'}
      </button>
      
      {debugResult && (
        <pre className="debug-results">
          {debugResult}
        </pre>
      )}
      
      <div className="debug-tips">
        <h4>Debugging Tips:</h4>
        <ul>
          <li>Check if your Payer Account ID exists in the database (use the diagnostics above)</li>
          <li>Verify the format of your Invoice ID or Bill Period Start Date</li>
          <li>Examine the Lambda function logs in CloudWatch</li>
          <li>Verify DynamoDB table permissions and structure</li>
          <li>Ensure data has been properly ingested into the DynamoDB table</li>
          <li>Try using one of the payer account IDs shown in the diagnostics</li>
        </ul>
      </div>
    </div>
  );
};

export default ApiDebugger;