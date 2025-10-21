import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                ✈️ Plan My Trip
              </h1>
            </div>
            <Link
              to="/app"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold mb-8">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Plan Your Perfect Trip
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              AI-powered travel planning with interactive maps, voice assistance, and personalized itineraries. 
              Discover amazing places and create unforgettable memories.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/app"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 transform hover:scale-105 shadow-xl hover:shadow-2xl"
              >
                🚀 Start Planning
              </Link>
              <button className="bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 border border-white/20">
                📖 Learn More
              </button>
            </div>
          </div>
        </div>

        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl"></div>
          <div className="absolute top-40 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-1/4 w-80 h-80 bg-pink-500/20 rounded-full blur-3xl"></div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Why Choose Plan My Trip?
              </span>
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Experience the future of travel planning with our cutting-edge AI technology
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🤖
              </div>
              <h3 className="text-2xl font-semibold mb-4">AI-Powered Planning</h3>
              <p className="text-gray-300 leading-relaxed">
                Our advanced AI understands your preferences and creates personalized itineraries tailored to your interests and travel style.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🗺️
              </div>
              <h3 className="text-2xl font-semibold mb-4">Interactive Maps</h3>
              <p className="text-gray-300 leading-relaxed">
                Visualize your journey with beautiful, interactive maps that show your route and help you navigate between destinations.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🎤
              </div>
              <h3 className="text-2xl font-semibold mb-4">Voice Assistant</h3>
              <p className="text-gray-300 leading-relaxed">
                Talk to our AI assistant naturally. Ask questions, make changes, and get recommendations using voice commands.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                ⚡
              </div>
              <h3 className="text-2xl font-semibold mb-4">Real-time Updates</h3>
              <p className="text-gray-300 leading-relaxed">
                Get instant updates and modifications to your itinerary. Our AI adapts to your feedback in real-time.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                🎯
              </div>
              <h3 className="text-2xl font-semibold mb-4">Personalized Recommendations</h3>
              <p className="text-gray-300 leading-relaxed">
                Discover hidden gems and local favorites based on your interests, budget, and travel preferences.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-rose-500 rounded-2xl flex items-center justify-center text-2xl mb-6">
                📱
              </div>
              <h3 className="text-2xl font-semibold mb-4">Mobile Friendly</h3>
              <p className="text-gray-300 leading-relaxed">
                Access your itinerary anywhere, anytime. Our responsive design works perfectly on all devices.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="py-20 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Choose Your Plan
              </span>
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Start free and upgrade when you're ready for unlimited adventures
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Freemium Plan */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 hover:bg-white/10 transition-all duration-300 relative">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-4">
                  🆓
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Freemium</h3>
                <div className="text-4xl font-bold text-white mb-2">Free</div>
                <p className="text-gray-400">Perfect for getting started</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">3 trip plans per month</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">Basic AI recommendations</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">Interactive maps</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">1-day itinerary max</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">Basic voice commands</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-green-400 text-lg">✓</span>
                  <span className="text-gray-300">Community support</span>
                </li>
              </ul>

              <Link
                to="/app"
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3 px-6 rounded-xl font-semibold text-center block transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                Start Free
              </Link>
            </div>

            {/* Premium Plan */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border-2 border-purple-500/50 hover:bg-white/15 transition-all duration-300 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-2 rounded-full text-sm font-semibold shadow-lg">
                  Most Popular
                </span>
              </div>

              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-4">
                  ⭐
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Premium</h3>
                <div className="text-4xl font-bold text-white mb-2">$9.99<span className="text-lg text-gray-400">/month</span></div>
                <p className="text-gray-400">For serious travelers</p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-white font-medium">Unlimited trip plans</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Advanced AI personalization</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Route optimization</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Multi-day itineraries (up to 30 days)</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Advanced voice assistant</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Priority support</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Export to PDF/Calendar</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Offline maps</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Weather integration</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Budget tracking</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">✓</span>
                  <span className="text-gray-300">Group trip planning</span>
                </li>
              </ul>

              <button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg">
                Upgrade to Premium
              </button>
            </div>
          </div>

          {/* Additional Info */}
          <div className="text-center mt-12">
            <p className="text-gray-400 mb-4">
              All plans include our core AI-powered trip planning features
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
              <span>✓ 30-day money-back guarantee</span>
              <span>✓ Cancel anytime</span>
              <span>✓ Secure payment</span>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Ready to Start Your Journey?
            </span>
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of travelers who have discovered their perfect trips with our AI-powered platform.
          </p>
          <Link
            to="/app"
            className="inline-block bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-12 py-4 rounded-xl font-semibold text-xl transition-all duration-200 transform hover:scale-105 shadow-xl hover:shadow-2xl"
          >
            🚀 Plan My Trip Now
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-black/40 backdrop-blur-sm border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
              ✈️ Plan My Trip
            </h3>
            <p className="text-gray-400 mb-6">
              AI-powered travel planning for the modern explorer
            </p>
            <div className="flex justify-center space-x-6">
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Terms of Service
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Contact
              </a>
            </div>
            <p className="text-gray-500 text-sm mt-6">
              © 2024 Plan My Trip. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
