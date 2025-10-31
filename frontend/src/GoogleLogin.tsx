import React, { useEffect, useState } from 'react';
import { GoogleLogin as GoogleLoginButton, CredentialResponse } from '@react-oauth/google';
import { useAuth } from './AuthContext';

interface GoogleLoginProps {
  onSuccess?: () => void;
  onError?: () => void;
  className?: string;
  text?: string;
  variant?: 'default' | 'outline' | 'minimal';
}

const GoogleLogin: React.FC<GoogleLoginProps> = ({ 
  onSuccess, 
  onError, 
  className = '',
  text = 'Continue with Google',
  variant = 'default'
}) => {
  const { login } = useAuth();
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  if (!clientId || clientId === 'your-google-client-id-here') {
    return (
      <div className={`${className} p-4 bg-yellow-500/20 border border-yellow-500/50 rounded-lg`}>
        <div className="text-yellow-200 text-base text-center">
          <div className="font-semibold mb-1 text-lg">⚠️ Google OAuth Not Configured</div>
          <div className="text-sm">
            Please set VITE_GOOGLE_CLIENT_ID in your .env file
          </div>
        </div>
      </div>
    );
  }

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      if (credentialResponse.credential) {
        // Decode the JWT token to get user info
        const base64Url = credentialResponse.credential.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        
        const userData = JSON.parse(jsonPayload);
        
        const user = {
          id: userData.sub,
          name: userData.name,
          email: userData.email,
          picture: userData.picture,
        };
        
        await login(user);
        onSuccess?.();
      }
    } catch (error) {
      console.error('Error processing Google login:', error);
      onError?.();
    }
  };

  const handleError = () => {
    console.error('Google login failed');
    onError?.();
  };

  const getButtonStyle = () => {
    switch (variant) {
      case 'outline':
        return 'bg-transparent border-2 border-white/20 hover:border-white/40 text-white hover:bg-white/10';
      case 'minimal':
        return 'bg-white/10 hover:bg-white/20 text-white border border-white/20 hover:border-white/40';
      default:
        return 'bg-white hover:bg-gray-100 text-gray-900 border border-gray-300 hover:border-gray-400';
    }
  };

  // Track viewport to adjust button sizing on mobile
  const [isMobile, setIsMobile] = useState<boolean>(typeof window !== 'undefined' ? window.matchMedia('(max-width: 767px)').matches : false);

  useEffect(() => {
    const mql = window.matchMedia('(max-width: 767px)');
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    if (mql.addEventListener) mql.addEventListener('change', handler);
    else mql.addListener(handler);
    return () => {
      if (mql.removeEventListener) mql.removeEventListener('change', handler);
      else mql.removeListener(handler);
    };
  }, []);

  return (
    <div className={`google-login-wrapper ${className}`}>
      <style dangerouslySetInnerHTML={{
        __html: `
          .google-login-wrapper iframe { font-size: ${isMobile ? '14px' : '18px'} !important; }
          .google-login-wrapper div[role="button"] {
            font-size: ${isMobile ? '14px' : '18px'} !important;
            font-weight: 600 !important;
            height: ${isMobile ? '40px' : '52px'} !important;
            min-height: ${isMobile ? '40px' : '52px'} !important;
          }
          .google-login-wrapper div[role="button"] span { font-size: ${isMobile ? '14px' : '18px'} !important; font-weight: 600 !important; }
          .google-login-wrapper div[role="button"] div  { font-size: ${isMobile ? '14px' : '18px'} !important; font-weight: 600 !important; }
        `
      }} />
      <GoogleLoginButton
        onSuccess={handleSuccess}
        onError={handleError}
        useOneTap={false}
        theme="outline"
        size={isMobile ? 'medium' : 'large'}
        text="continue_with"
        shape="rectangular"
        logo_alignment="left"
        width="100%"
        locale="en"
      />
    </div>
  );
};

export default GoogleLogin;
