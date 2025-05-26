// frontend/src/App.tsx
import React, { useState } from 'react';
// You might want to remove or clear content from App.css if you want absolutely no styling
// import './App.css';

function App() {
  const [itemId, setItemId] = useState('');
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // IMPORTANT: This API_ENDPOINT will be replaced during the build process by Vite
  // based on the .env.production (or .env.development) file.
  // For local development, you might use a placeholder like 'http://localhost:3000/query'
  // but for deployment, it will be the actual API Gateway URL.
  const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT || 'http://localhost:3000/query';

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault(); // Prevent default form submission behavior (page reload)
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch(`${API_ENDPOINT}?id=${encodeURIComponent(itemId)}`);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || 'Failed to fetch data from API.');
      }

      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#f0f0f0', // Light grey background
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '8px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        maxWidth: '400px',
        width: '100%',
        textAlign: 'center'
      }}>
        <h1>BillQuest Data Lookup</h1>

        <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
          <div>
            <label htmlFor="itemId" style={{ display: 'block', marginBottom: '5px' }}>
              Item ID:
            </label>
            <input
              type="text"
              id="itemId"
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              required
              style={{
                width: 'calc(100% - 22px)', // Account for padding
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                marginBottom: '15px'
              }}
              placeholder="e.g., INV001"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#007bff', // Blue button
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Querying...' : 'Query Data'}
          </button>
        </form>

        {loading && (
          <p style={{ marginTop: '20px', color: '#007bff' }}>Loading data...</p>
        )}

        {error && (
          <p style={{ marginTop: '20px', color: 'red' }}>Error: {error}</p>
        )}

        {data && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f9f9f9',
            border: '1px solid #eee',
            borderRadius: '4px',
            textAlign: 'left',
            overflowX: 'auto',
            maxHeight: '200px'
          }}>
            <h2>Result:</h2>
            <pre style={{ margin: '0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;