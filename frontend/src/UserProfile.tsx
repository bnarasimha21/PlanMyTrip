import React, { useState, useEffect, useRef } from 'react';
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
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/10 transition-colors duration-200"
      >
        <img
          src={user.picture || '/default-avatar.png'}
          alt={user.name}
          className="w-8 h-8 rounded-full border-2 border-white/20"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=6366f1&color=fff&size=32`;
          }}
        />
        <div className="text-left">
          <div className="text-base font-semibold text-blue-600">{user.name}</div>
          <div className="text-sm text-slate-600">{user.email}</div>
        </div>
        {showDropdown && (
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
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
        <div className="absolute -right-8 mt-2 w-64 sm:w-72 max-w-[calc(100vw-4rem)] bg-white/95 backdrop-blur-sm rounded-xl border border-blue-200 shadow-xl z-[100]">
          <div className="p-4 border-b border-blue-200">
            <div className="flex items-center gap-3">
              <img
                src={user.picture || '/default-avatar.png'}
                alt={user.name}
                className="w-12 h-12 rounded-full border-2 border-blue-200"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=0ea5e9&color=fff&size=48`;
                }}
              />
              <div>
                <div className="text-lg font-semibold text-slate-800">{user.name}</div>
                <div className="text-base text-slate-600">{user.email}</div>
              </div>
            </div>
          </div>
          
          <div className="p-3">
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
