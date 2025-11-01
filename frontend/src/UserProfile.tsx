import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
const API_BASE = (import.meta as any).env.VITE_API_BASE || window.location.origin;
import { useAuth } from './AuthContext';

interface UserProfileProps {
  className?: string;
  showDropdown?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({ 
  className = '', 
  showDropdown = true 
}) => {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [dropdownTop, setDropdownTop] = useState<number>(0);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Detect mobile viewport - must be defined before useEffects that use it
  const [isMobile, setIsMobile] = useState<boolean>(typeof window !== 'undefined' ? window.innerWidth <= 767 : false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 767);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const fetchRole = async () => {
      if (!user) return;
      
      // Retry mechanism for mobile reliability
      const fetchWithRetry = async (retries = 3): Promise<void> => {
        try {
          const resp = await fetch(`${API_BASE}/user/${user.id}`);
          if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
          }
          const data = await resp.json();
          
          if (data.success && data.user) {
            // Check multiple variations: 1, true, 'admin' role
            const adminFlag = 
              data.user.IsAdmin === 1 || 
              data.user.IsAdmin === true || 
              data.user.isAdmin === 1 || 
              data.user.isAdmin === true ||
              data.user.IsAdmin === '1' ||
              data.user.isAdmin === '1' ||
              data.user.role === 'admin' ||
              data.user.role === 'Admin' ||
              data.user.Role === 'admin' ||
              data.user.Role === 'Admin';
            setIsAdmin(!!adminFlag);
            return; // Success, no retry needed
          }
          throw new Error('Invalid response format');
        } catch (error) {
          if (retries > 0) {
            // Retry after a short delay
            await new Promise(resolve => setTimeout(resolve, 500));
            return fetchWithRetry(retries - 1);
          }
          // All retries failed, default to false
          setIsAdmin(false);
        }
      };
      
      fetchWithRetry();
    };
    
    fetchRole();
  }, [user]);

  // Calculate dropdown position on mobile when it opens
  useEffect(() => {
    if (isDropdownOpen && isMobile && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownTop(rect.bottom + 8);
    }
  }, [isDropdownOpen, isMobile]);

  // Debug log when dropdown opens
  useEffect(() => {
    if (isDropdownOpen) {
      console.log('🔍 Dropdown rendering - isAdmin:', isAdmin, 'user:', user);
      console.log('🔍 Mobile:', isMobile);
      console.log('🔍 Dropdown open:', isDropdownOpen);
    }
  }, [isDropdownOpen, isAdmin, user, isMobile]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  if (!user) return null;

  const handleLogout = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('🔄 Sign out button clicked');
    
    // Close dropdown first
    setIsDropdownOpen(false);
    
    // Then logout with a small delay to ensure dropdown closes
    setTimeout(() => {
      logout();
      console.log('✅ Sign out completed');
    }, 100);
  };

  return (
    <div ref={dropdownRef} className={`relative ${className} ${isDropdownOpen && isMobile ? 'dropdown-open-mobile' : ''}`} style={{ zIndex: isDropdownOpen && isMobile ? 9999 : 'auto' }}>
      <button
        ref={buttonRef}
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
      >
        <span className={`${isMobile ? 'text-sm' : 'text-base'}`}>{user.name}</span>
        {showDropdown && (
          <svg
            className={`${isMobile ? 'w-3 h-3' : 'w-4 h-4'} transition-transform duration-200 ${
              isDropdownOpen ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {showDropdown && isDropdownOpen && (
        <div 
          className={`${isMobile ? 'fixed' : 'absolute'} ${isMobile ? 'right-4' : 'right-0'} ${isMobile ? '' : 'mt-2'} ${isMobile ? 'w-56' : 'w-64'} max-w-[calc(100vw-2rem)] bg-white/95 backdrop-blur-sm rounded-xl border border-blue-200 shadow-xl`} 
          style={{ 
            zIndex: 9999,
            ...(isMobile && { top: `${dropdownTop}px` })
          }}
        >
          <div className="p-3 space-y-2" style={{ overflow: 'visible', minHeight: 'auto' }}>
            {isAdmin && (
              <Link
                to="/admin"
                onClick={() => setIsDropdownOpen(false)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors duration-200 text-base font-medium cursor-pointer"
                style={{ 
                  display: 'flex', 
                  visibility: 'visible', 
                  opacity: 1,
                  order: isMobile ? -1 : 0,
                  minHeight: '44px',
                  width: '100%',
                  position: 'relative',
                  zIndex: 11
                }}
              >
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3-1.343-3-3-3zm8.485 3a8.485 8.485 0 11-16.97 0 8.485 8.485 0 0116.97 0z" />
                </svg>
                <span>Dashboard</span>
              </Link>
            )}
            <Link
              to="/settings"
              onClick={() => setIsDropdownOpen(false)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200 text-base font-medium cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </Link>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-left text-red-500 hover:bg-red-50 rounded-lg transition-colors duration-200 text-base font-medium cursor-pointer"
              type="button"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
