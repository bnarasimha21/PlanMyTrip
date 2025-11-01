import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import GoogleLogin from './GoogleLogin';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    // If already authenticated, redirect to app
    if (!isLoading && isAuthenticated) {
      navigate('/app');
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleLoginSuccess = () => {
    // Redirect to app after successful login
    navigate('/app');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-8 border border-blue-200 shadow-xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent mb-2">
              ✈️ TripXplorer
            </h1>
            <p className="text-slate-600 text-lg">Welcome back! Please sign in to continue.</p>
          </div>

          <div className="space-y-4 flex justify-center">
            <div className="w-full">
              <GoogleLogin
                onSuccess={handleLoginSuccess}
                className="w-full"
                text="Continue with Google"
                variant="default"
              />
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-500">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

