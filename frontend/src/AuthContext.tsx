import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Extend Window interface for Google OAuth
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          disableAutoSelect: () => void;
          revoke: () => void;
        };
      };
    };
  }
}

interface User {
  id: string;
  name: string;
  email: string;
  picture?: string;
}

interface AuthContextType {
  user: User | null;
  login: (userData: User) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in from localStorage
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (userData: User) => {
    try {
      // Check if user exists in database, create if not
      await createOrUpdateUser(userData);
      
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Error during login:', error);
      // Still set user locally even if database call fails
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    }
  };

  const createOrUpdateUser = async (userData: User) => {
    const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8000';
    
    try {
      // First, try to get the user to see if they exist
      const response = await fetch(`${API_BASE}/user/${userData.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      if (!data.success) {
        // User doesn't exist, create them
        const createResponse = await fetch(`${API_BASE}/user/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userData.id,
            email: userData.email,
            name: userData.name,
            google_id: userData.id
          }),
        });

        const createData = await createResponse.json();
        
        if (createData.success) {
          console.log('✅ User created successfully in database');
        } else {
          console.error('❌ Failed to create user:', createData.error);
        }
      } else {
        console.log('✅ User already exists in database');
      }
    } catch (error) {
      console.error('Error checking/creating user:', error);
      throw error;
    }
  };

  const logout = () => {
    console.log('🔄 AuthContext logout called');
    console.log('Current user before logout:', user);
    
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('subscription_plan');
    console.log('✅ Local storage cleared');
    
    // Clear Google OAuth session if available
    if (typeof window !== 'undefined' && window.google) {
      try {
        window.google.accounts.id.disableAutoSelect();
        window.google.accounts.id.revoke();
        console.log('✅ Google OAuth session cleared');
      } catch (error) {
        console.log('Google OAuth sign-out not available:', error);
      }
    } else {
      console.log('ℹ️ Google OAuth not available for sign-out');
    }
    
    console.log('✅ AuthContext logout completed');
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
