import React, { createContext, useContext, useState, useEffect } from 'react';

interface SubscriptionContextType {
  isSubscribed: boolean;
  subscriptionPlan: string | null;
  setSubscription: (plan: string) => void;
  clearSubscription: () => void;
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

  useEffect(() => {
    // Check localStorage for existing subscription
    const savedSubscription = localStorage.getItem('subscription_plan');
    if (savedSubscription) {
      setSubscriptionPlan(savedSubscription);
      setIsSubscribed(true);
    }

    // Listen for subscription updates from payment
    const handleSubscriptionUpdate = (event: CustomEvent) => {
      const { plan, isSubscribed } = event.detail;
      setSubscriptionPlan(plan);
      setIsSubscribed(isSubscribed);
    };

    window.addEventListener('subscriptionUpdated', handleSubscriptionUpdate as EventListener);

    return () => {
      window.removeEventListener('subscriptionUpdated', handleSubscriptionUpdate as EventListener);
    };
  }, []);

  const setSubscription = (plan: string) => {
    setSubscriptionPlan(plan);
    setIsSubscribed(true);
    localStorage.setItem('subscription_plan', plan);
  };

  const clearSubscription = () => {
    setSubscriptionPlan(null);
    setIsSubscribed(false);
    localStorage.removeItem('subscription_plan');
  };

  const value = {
    isSubscribed,
    subscriptionPlan,
    setSubscription,
    clearSubscription,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};
