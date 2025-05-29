import { useEffect, useState } from 'react';
import { getCurrentUser } from '../aws/auth';
import { useNavigate } from 'react-router-dom';
import { signOut } from 'aws-amplify/auth';

function Header() {
  const [userEmail, setUserEmail] = useState<string>('');
  const navigate = useNavigate();

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

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <h1>BillQuest</h1>
        {userEmail && (
          <div className="user-info">
            <span className="user-email">{userEmail}</span>
            <button onClick={handleLogout} className="logout-button">
              Log Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;