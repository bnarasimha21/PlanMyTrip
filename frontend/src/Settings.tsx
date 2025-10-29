import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { useSubscription } from './SubscriptionContext';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const { subscriptionPlan, usage, limits, refreshUsage, setSubscription } = useSubscription();
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [localSubscriptionPlan, setLocalSubscriptionPlan] = useState<string | null>(subscriptionPlan);
  
  // Update local state when subscriptionPlan changes
  useEffect(() => {
    setLocalSubscriptionPlan(subscriptionPlan);
  }, [subscriptionPlan]);

  const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8000';

  const updateSubscription = async (newPlan: string) => {
    if (!user) return;

    // Check against current plan (local state or context)
    const currentPlan = localSubscriptionPlan || subscriptionPlan;
    if (currentPlan === newPlan) {
      setMessage({ type: 'error', text: `You are already on the ${newPlan} plan.` });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_BASE}/subscription/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          subscription_plan: newPlan,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Update local state immediately to reflect changes in UI
        setLocalSubscriptionPlan(newPlan);
        
        setMessage({ 
          type: 'success', 
          text: `Successfully ${newPlan === 'premium' ? 'upgraded to' : 'downgraded to'} ${newPlan} plan!` 
        });
        
        // Update subscription context immediately
        if (setSubscription) {
          setSubscription(newPlan);
        }
        
        // Update localStorage
        localStorage.setItem('subscription_plan', newPlan);
        
        // Dispatch event to update subscription context
        window.dispatchEvent(new CustomEvent('subscriptionUpdated', {
          detail: { plan: newPlan, isSubscribed: newPlan === 'premium' }
        }));
        
        // Refresh usage data
        setTimeout(() => {
          refreshUsage();
        }, 500);
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update subscription. Please try again.' });
      }
    } catch (error) {
      console.error('Error updating subscription:', error);
      setMessage({ type: 'error', text: 'An error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-800 mb-4">Please log in to access settings</h2>
          <Link
            to="/"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Go to Home
          </Link>
        </div>
      </div>
    );
  }

  // Use local state for immediate UI updates, fallback to context if local state is null
  const currentPlan = localSubscriptionPlan || subscriptionPlan;
  const isPremium = currentPlan === 'premium';
  const tripsUsed = usage?.trips_used || 0;
  const maxTrips = limits?.max_trips_per_month || 3;
  const isUnlimited = maxTrips === -1;

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 text-slate-800">
      {/* Header */}
      <div className="bg-white/90 backdrop-blur-md border-b border-blue-200 shadow-lg relative z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link to="/" className="inline-block group">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
                ✈️ TripXplorer
              </h1>
            </Link>
            <Link
              to="/app"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white rounded-lg font-medium transition-all duration-200"
            >
              Back to App
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-blue-200 p-8">
          <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
            Settings
          </h2>
          <p className="text-slate-600 mb-8">Manage your account and subscription</p>

          {/* Current Subscription Section */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-slate-800 mb-4">Current Subscription</h3>
            <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-xl p-6 border border-blue-200">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-4 py-2 rounded-lg text-base font-semibold ${
                      isPremium
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-yellow-900 shadow-sm'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {isPremium ? '⭐ Premium' : '🆓 Freemium'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600">
                    {isUnlimited ? (
                      <span className="text-green-600 font-medium">Unlimited trips this month</span>
                    ) : (
                      <span>
                        {tripsUsed} / {maxTrips} trips used this month
                      </span>
                    )}
                  </p>
                  {limits?.max_days_per_trip && (
                    <p className="text-sm text-slate-600 mt-1">
                      Max {limits.max_days_per_trip} day{limits.max_days_per_trip !== 1 ? 's' : ''} per trip
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Change Subscription Section */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-slate-800 mb-4">Change Subscription Plan</h3>
            <div className="space-y-4">
              {/* Upgrade to Premium */}
              {!isPremium && (
                <div className="bg-white border-2 border-blue-300 rounded-xl p-6 hover:shadow-lg transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold text-slate-800 mb-2">⭐ Premium Plan</h4>
                      <ul className="text-sm text-slate-600 space-y-1 mb-4">
                        <li>• Unlimited trip plans</li>
                        <li>• Multi-day itineraries (up to 30 days)</li>
                        <li>• Advanced AI features</li>
                        <li>• All premium features</li>
                      </ul>
                    </div>
                    <button
                      onClick={() => updateSubscription('premium')}
                      disabled={isLoading}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ml-4"
                    >
                      {isLoading ? 'Updating...' : 'Upgrade to Premium'}
                    </button>
                  </div>
                </div>
              )}

              {/* Downgrade to Freemium */}
              {isPremium && (
                <div className="bg-white border-2 border-blue-200 rounded-xl p-6 hover:shadow-lg transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold text-slate-800 mb-2">🆓 Freemium Plan</h4>
                      <ul className="text-sm text-slate-600 space-y-1 mb-4">
                        <li>• 3 trip plans per month</li>
                        <li>• 1 day per trip maximum</li>
                        <li>• Basic AI features</li>
                        <li>• Community support</li>
                      </ul>
                      <p className="text-xs text-slate-500 italic">
                        Note: Downgrading will limit your access to premium features.
                      </p>
                    </div>
                    <button
                      onClick={() => updateSubscription('freemium')}
                      disabled={isLoading}
                      className="px-6 py-3 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ml-4"
                    >
                      {isLoading ? 'Updating...' : 'Downgrade to Freemium'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Message Display */}
          {message && (
            <div className={`mb-6 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200 text-green-800'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}>
              <div className="flex items-center gap-2">
                <span>{message.type === 'success' ? '✅' : '❌'}</span>
                <span>{message.text}</span>
              </div>
            </div>
          )}

          {/* Note */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Payment integration will be added later. For now, subscription changes are directly updated in the database.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;

