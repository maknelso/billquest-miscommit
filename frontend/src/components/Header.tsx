import { useState } from 'react';
// Authentication imports commented out for development
// import { getCurrentUser } from '../aws/auth';
// import { useNavigate } from 'react-router-dom';
// import { signOut } from 'aws-amplify/auth';

function Header() {
  // For development, hardcode a demo user or leave blank
  const [userEmail, setUserEmail] = useState<string>('demo@example.com');
  // const navigate = useNavigate();

  // Authentication useEffect commented out for development
  /*
  useEffect(() => {
    async function fetchUserInfo() {
      try {
        const user = await getCurrentUser();
        if (user && user.signInDetails?.loginId) {
          setUserEmail(user.signInDetails.loginId);
        }
      } catch (error) {
        console.error('Error fetching user info:', error);
      }
    }

    fetchUserInfo();
  }, []);
  */

  // Simplified logout for development
  const handleLogout = () => {
    alert('Logout functionality disabled during development');
    // In production:
    // try {
    //   await signOut();
    //   navigate('/login');
    // } catch (error) {
    //   console.error('Error signing out:', error);
    // }
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <h1>BillQuest</h1>
        <nav className="main-nav">
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/dashboard">Dashboard</a></li>
          </ul>
        </nav>
        {userEmail && (
          <div className="user-info">
            <span className="user-email">{userEmail}</span>
            <button onClick={handleLogout} className="logout-button">
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;