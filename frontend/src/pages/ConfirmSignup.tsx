import { useState, FormEvent } from 'react';
import { confirmSignUp } from 'aws-amplify/auth';
import { useNavigate, useLocation } from 'react-router-dom';

function ConfirmSignup() {
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get username from state or query params
  const username = location.state?.username || new URLSearchParams(location.search).get('username') || '';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!username) {
      setError('Username is required. Please go back to signup.');
      setIsLoading(false);
      return;
    }

    try {
      await confirmSignUp({ username, confirmationCode: code });
      alert('Account confirmed successfully! You can now log in.');
      navigate('/login');
    } catch (err) {
      console.error('Confirmation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to confirm signup');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="confirm-container">
      <form onSubmit={handleSubmit} className="confirm-form">
        <h2>Confirm Your Account</h2>
        <p>Please enter the verification code sent to your email.</p>
        
        {error && <p className="error-message">{error}</p>}
        
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => {}} // Read-only
            disabled
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="code">Verification Code</label>
          <input
            type="text"
            id="code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
          />
        </div>
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Confirming...' : 'Confirm Account'}
        </button>
        
        <p className="login-link">
          <a href="#" onClick={() => navigate('/login')}>Back to Login</a>
        </p>
      </form>
    </div>
  );
}

export default ConfirmSignup;