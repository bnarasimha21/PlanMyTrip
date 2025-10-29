import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { useSubscription } from './SubscriptionContext';
import GoogleLogin from './GoogleLogin';
import UserProfile from './UserProfile';
import SetupGuide from './SetupGuide';
import PaymentModal from './PaymentModal';
import SubscriptionStatus from './SubscriptionStatus';

const HomePage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const { isSubscribed, subscriptionPlan } = useSubscription();
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<{
    name: string;
    price: number;
    features: string[];
  } | null>(null);

  const premiumPlan = {
    name: 'Premium',
    price: 1.00,
    features: [
      'Unlimited trip plans',
      'Advanced AI personalization',
      'Route optimization',
      'Multi-day itineraries (up to 30 days)',
      'Advanced voice assistant',
      'Priority support',
      'Export to PDF/Calendar',
      'Offline maps',
      'Weather integration',
      'Budget tracking',
      'Group trip planning'
    ]
  };

  const handleUpgradeClick = () => {
    setSelectedPlan(premiumPlan);
    setShowPaymentModal(true);
  };

  const handleLearnMoreClick = () => {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
      featuresSection.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 text-slate-800 overflow-x-hidden">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-blue-200 shadow-sm relative z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
                ✈️ TripXplorer
              </h1>
            </div>
            <div className="flex items-center gap-4 relative z-50">
              {isLoading ? (
                <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              ) : (
                <>
                  <SubscriptionStatus />
                  {isAuthenticated ? (
                    <UserProfile />
                  ) : (
                    <GoogleLogin 
                      className="w-48"
                      onSuccess={() => console.log('Login successful')}
                    />
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold mb-8">
              <span className="bg-gradient-to-r from-blue-600 via-sky-600 to-blue-500 bg-clip-text text-transparent">
                Plan Your Perfect Trip
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 mb-6 max-w-3xl mx-auto leading-relaxed">
              AI-powered travel planning with interactive maps, voice assistance, and personalized itineraries. 
              Discover amazing places and create unforgettable memories.
            </p>
            <div className="flex flex-row gap-3 justify-center">
              <Link
                to="/app"
                className="bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white px-6 py-3 rounded-lg font-medium text-base transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                🚀 Start Planning
              </Link>
              <button 
                onClick={handleLearnMoreClick}
                className="bg-white/80 hover:bg-white backdrop-blur-sm text-blue-600 px-6 py-3 rounded-lg font-medium text-base transition-all duration-200 border border-blue-200 shadow-lg hover:shadow-xl"
              >
                📖 Learn More
              </button>
            </div>
          </div>
        </div>

        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-200/30 rounded-full blur-3xl"></div>
          <div className="absolute top-40 right-10 w-96 h-96 bg-sky-200/30 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-1/4 w-80 h-80 bg-blue-100/40 rounded-full blur-3xl"></div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="py-20 bg-blue-50/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
                Why Choose TripXplorer?
              </span>
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Experience the future of travel planning with our cutting-edge AI technology
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🤖
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">AI-Powered Planning</h3>
              <p className="text-slate-600 leading-relaxed">
                Our advanced AI understands your preferences and creates personalized itineraries tailored to your interests and travel style.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-sky-500 to-blue-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🗺️
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">Interactive Maps</h3>
              <p className="text-slate-600 leading-relaxed">
                Visualize your journey with beautiful, interactive maps that show your route and help you navigate between destinations.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-sky-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🎤
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">Voice Assistant</h3>
              <p className="text-slate-600 leading-relaxed">
                Talk to our AI assistant naturally. Ask questions, make changes, and get recommendations using voice commands.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-sky-400 to-blue-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                ⚡
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">Real-time Updates</h3>
              <p className="text-slate-600 leading-relaxed">
                Get instant updates and modifications to your itinerary. Our AI adapts to your feedback in real-time.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-600 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🎯
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">Personalized Recommendations</h3>
              <p className="text-slate-600 leading-relaxed">
                Discover hidden gems and local favorites based on your interests, budget, and travel preferences.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-sky-500 to-blue-600 rounded-2xl flex items-center justify-center text-2xl mb-6">
                📱
              </div>
              <h3 className="text-2xl font-semibold mb-4 text-slate-800">Mobile Friendly</h3>
              <p className="text-slate-600 leading-relaxed">
                Access your itinerary anywhere, anytime. Our responsive design works perfectly on all devices.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="py-20 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
                Choose Your Plan
              </span>
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Start free and upgrade when you're ready for unlimited adventures
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Freemium Plan */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 border border-blue-200 hover:bg-white hover:shadow-lg transition-all duration-300 relative">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-500 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-4">
                  🆓
                </div>
                <h3 className="text-2xl font-bold text-slate-800 mb-2">Freemium</h3>
                <div className="text-4xl font-bold text-slate-800 mb-2">Free</div>
                <p className="text-slate-600">Perfect for getting started</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">3 trip plans per month</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Basic AI recommendations</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Interactive maps</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">1-day itinerary max</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Basic voice commands</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Community support</span>
                </li>
              </ul>

              <Link
                to="/app"
                className="w-full bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white py-3 px-6 rounded-xl font-semibold text-center block transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                Start Free
              </Link>
            </div>

            {/* Premium Plan */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 border-2 border-blue-300 hover:bg-white hover:shadow-xl transition-all duration-300 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-blue-600 to-sky-600 text-white px-6 py-2 rounded-full text-sm font-semibold shadow-lg">
                  Most Popular
                </span>
              </div>

              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-500 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-4">
                  ⭐
                </div>
                <h3 className="text-2xl font-bold text-slate-800 mb-2">Premium</h3>
                <div className="text-4xl font-bold text-slate-800 mb-2">$1.00<span className="text-lg text-slate-600">/month</span></div>
                <p className="text-slate-600">For serious travelers</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-800 font-medium">Unlimited trip plans</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Advanced AI personalization</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Route optimization</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Multi-day itineraries (up to 30 days)</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Advanced voice assistant</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Priority support</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Export to PDF/Calendar</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Offline maps</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Weather integration</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Budget tracking</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-blue-500 text-lg">✓</span>
                  <span className="text-slate-600">Group trip planning</span>
                </li>
              </ul>

              <button 
                onClick={handleUpgradeClick}
                className="w-full bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                {isSubscribed ? 'Manage Subscription' : 'Upgrade to Premium'}
              </button>
            </div>
          </div>

          {/* Additional Info */}
          <div className="text-center mt-12">
            <p className="text-slate-600 mb-4">
              All plans include our core AI-powered trip planning features
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-500">
              <span>✓ 30-day money-back guarantee</span>
              <span>✓ Cancel anytime</span>
              <span>✓ Secure payment</span>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 bg-gradient-to-r from-blue-50 to-sky-50">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
              Ready to Start Your Journey?
            </span>
          </h2>
          <p className="text-xl text-slate-600 mb-8">
            Join thousands of travelers who have discovered their perfect trips with our AI-powered platform.
          </p>
          <Link
            to="/app"
            className="inline-block bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white px-12 py-4 rounded-xl font-semibold text-xl transition-all duration-200 transform hover:scale-105 shadow-xl hover:shadow-2xl"
          >
            🚀 TripXplorer Now
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-blue-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent mb-4">
              ✈️ TripXplorer
            </h3>
            <p className="text-slate-600 mb-6">
              AI-powered travel planning for the modern explorer
            </p>
            <div className="flex justify-center space-x-6">
              <a href="#" className="text-slate-500 hover:text-blue-600 transition-colors duration-200">
                Privacy Policy
              </a>
              <a href="#" className="text-slate-500 hover:text-blue-600 transition-colors duration-200">
                Terms of Service
              </a>
              <a href="#" className="text-slate-500 hover:text-blue-600 transition-colors duration-200">
                Contact
              </a>
            </div>
            <p className="text-slate-400 text-sm mt-6">
              © 2024 TripXplorer. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Setup Guide */}
      <SetupGuide />

      {/* Payment Modal */}
      {selectedPlan && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => {
            setShowPaymentModal(false);
            setSelectedPlan(null);
          }}
          plan={selectedPlan}
        />
      )}
    </div>
  );
};

export default HomePage;
