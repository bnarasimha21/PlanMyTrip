import React, { createContext, useContext, useState, useEffect } from 'react';

interface UsageInfo {
  trips_used: number;
  max_trips: number;
}

interface SubscriptionLimits {
  max_trips_per_month: number;
  max_days_per_trip: number;
  features: string[];
}

interface SubscriptionContextType {
  isSubscribed: boolean;
  subscriptionPlan: string | null;
  usage: UsageInfo | null;
  limits: SubscriptionLimits | null;
  setSubscription: (plan: string) => void;
  clearSubscription: () => void;
  checkUsage: (days?: number) => Promise<boolean>;
  refreshUsage: () => Promise<void>;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

interface SubscriptionProviderProps {
  children: React.ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionPlan, setSubscriptionPlan] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [limits, setLimits] = useState<SubscriptionLimits | null>(null);

  const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8000';

  const checkUsage = async (days?: number): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/subscription/usage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'default',
          subscription_plan: subscriptionPlan,
          days: days
        }),
      });

      const data = await response.json();
      
      if (data.success && data.allowed) {
        return true;
      } else {
        // Show error message to user
        if (data.message) {
          alert(data.message);
        }
        return false;
      }
    } catch (error) {
      console.error('Error checking usage:', error);
      return false;
    }
  };

  const refreshUsage = async () => {
    try {
      const response = await fetch(`${API_BASE}/subscription/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'default',
          subscription_plan: subscriptionPlan
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setUsage(data.usage);
        setLimits(data.limits);
        setSubscriptionPlan(data.subscription_plan);
        setIsSubscribed(data.subscription_plan === 'premium');
      }
    } catch (error) {
      console.error('Error refreshing usage:', error);
    }
  };

  useEffect(() => {
    // Check localStorage for existing subscription
    const savedSubscription = localStorage.getItem('subscription_plan');
    if (savedSubscription) {
      setSubscriptionPlan(savedSubscription);
      setIsSubscribed(savedSubscription === 'premium');
    }

    // Refresh usage data
    refreshUsage();

    // Listen for subscription updates from payment
    const handleSubscriptionUpdate = (event: CustomEvent) => {
      const { plan, isSubscribed } = event.detail;
      setSubscriptionPlan(plan);
      setIsSubscribed(isSubscribed);
      // Refresh usage after subscription change
      setTimeout(() => refreshUsage(), 1000);
    };

    window.addEventListener('subscriptionUpdated', handleSubscriptionUpdate as EventListener);

    return () => {
      window.removeEventListener('subscriptionUpdated', handleSubscriptionUpdate as EventListener);
    };
  }, []);

  const setSubscription = (plan: string) => {
    setSubscriptionPlan(plan);
    setIsSubscribed(plan === 'premium');
    localStorage.setItem('subscription_plan', plan);
    // Refresh usage after subscription change
    setTimeout(() => refreshUsage(), 1000);
  };

  const clearSubscription = () => {
    setSubscriptionPlan(null);
    setIsSubscribed(false);
    setUsage(null);
    setLimits(null);
    localStorage.removeItem('subscription_plan');
  };

  const value = {
    isSubscribed,
    subscriptionPlan,
    usage,
    limits,
    setSubscription,
    clearSubscription,
    checkUsage,
    refreshUsage,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};
