import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './AuthContext';
import { SubscriptionProvider } from './SubscriptionContext';
import HomePage from './HomePage';
import TripPlanner from './TripPlanner';
import Settings from './Settings';
import AdminDashboard from './AdminDashboard';
import LoginPage from './LoginPage';

// You'll need to get this from Google Cloud Console
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === 'your-google-client-id-here') {
  console.warn('⚠️ VITE_GOOGLE_CLIENT_ID is not set. Please add it to your .env file');
}

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <SubscriptionProvider>
          <Router>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/app" element={<TripPlanner />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/admin" element={<AdminDashboard />} />
            </Routes>
          </Router>
        </SubscriptionProvider>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;