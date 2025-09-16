import React from 'react';

export default function TestTailwind() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
      <div className="bg-white/20 backdrop-blur-md rounded-2xl p-8 border border-white/30">
        <h1 className="text-4xl font-bold text-white mb-4">🎨 Tailwind CSS Test</h1>
        <p className="text-white/80 text-lg">If you can see this styled, Tailwind is working!</p>
        <button className="mt-4 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 transform hover:scale-105">
          Test Button
        </button>
      </div>
    </div>
  );
}
