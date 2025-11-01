import React, { useState, useEffect } from 'react';
import { useSubscription } from './SubscriptionContext';

interface SubscriptionStatusProps {
  className?: string;
}

const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({ className = '' }) => {
  const { subscriptionPlan, usage, limits } = useSubscription();
  const [isMobile, setIsMobile] = useState<boolean>(typeof window !== 'undefined' ? window.innerWidth <= 767 : false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 767);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Show only when we have at least some subscription data
  // This could be from localStorage (subscriptionPlan) or API (usage/limits)
  const hasData = subscriptionPlan || usage || limits;
  
  if (!hasData) {
    return null;
  }

  const isPremium = subscriptionPlan === 'premium';
  const tripsUsed = usage?.trips_used || 0;
  const maxTrips = limits?.max_trips_per_month || usage?.max_trips || 0;
  const isUnlimited = maxTrips === -1;

  return (
    <div className={`bg-gradient-to-r from-blue-50 to-sky-50 rounded-xl ${isMobile ? 'px-2.5 py-1.5' : 'px-4 py-2'} border border-blue-200 ${className}`}>
      <div className="flex items-center gap-2">
        <span className={`${isMobile ? 'px-1.5 py-0.5' : 'px-2.5 py-1'} rounded-lg text-xs font-semibold whitespace-nowrap ${
          isPremium
            ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-yellow-900 shadow-sm'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {isPremium ? (isMobile ? '⭐ Premium' : '⭐ Premium') : (isMobile ? '🆓 Free' : '🆓 Free')}
        </span>
        {isUnlimited ? (
          <span className={`${isMobile ? 'text-xs' : 'text-xs'} text-green-600 font-medium whitespace-nowrap`}>
            {isMobile ? '∞' : 'Unlimited'}
          </span>
        ) : maxTrips > 0 && (
          <span className={`${isMobile ? 'text-xs' : 'text-xs'} text-slate-600 whitespace-nowrap`}>
            {tripsUsed} / {maxTrips} trips
          </span>
        )}
      </div>
    </div>
  );
};

export default SubscriptionStatus;

