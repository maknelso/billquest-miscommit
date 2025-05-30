// Authentication config commented out for development
// import './aws/amplifyConfig';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App.tsx';
// Authentication pages commented out for development
// import Login from './pages/Login.tsx';
// import Signup from './pages/Signup.tsx';
// import ConfirmSignup from './pages/ConfirmSignup.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Authentication routes commented out for development */}
        {/* <Route path="/login" element={<Login />} /> */}
        {/* <Route path="/signup" element={<Signup />} /> */}
        {/* <Route path="/confirm" element={<ConfirmSignup />} /> */}
        <Route path="/" element={<App />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);