import React, { useState } from 'react';

const SetupGuide: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full shadow-lg transition-colors duration-200"
        title="Setup Guide"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute bottom-16 right-0 w-96 bg-slate-800/95 backdrop-blur-sm rounded-xl border border-slate-600 shadow-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Google OAuth Setup</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4 text-sm text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">1. Create Google OAuth Credentials</h4>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">Google Cloud Console</a></li>
                <li>Create a new project or select existing one</li>
                <li>Enable Google+ API</li>
                <li>Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"</li>
                <li>Set application type to "Web application"</li>
                <li>Add authorized origins: <code className="bg-slate-700 px-1 rounded">http://localhost:5174</code></li>
              </ol>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-2">2. Create .env file</h4>
              <p className="mb-2">Create a <code className="bg-slate-700 px-1 rounded">.env</code> file in the frontend directory:</p>
              <pre className="bg-slate-900 p-3 rounded text-xs overflow-x-auto">
{`VITE_GOOGLE_CLIENT_ID=286032655495-8ud7cg150qg3vavh6bm889uah3sstc94.apps.googleusercontent.com
VITE_API_BASE=http://localhost:8000
VITE_MAPBOX_TOKEN=pk.eyJ1IjoiYm5hcmFzaW1oYTIxIiwiYSI6ImNtOGQ1M2VzbDFhOXoyaXM1N3h4NW9reTMifQ.A1qPIVIJyq-wHWJkiYBadg`}
              </pre>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-2">3. Restart Development Server</h4>
              <p>After adding the .env file, restart your development server:</p>
              <code className="bg-slate-700 px-2 py-1 rounded text-xs block mt-1">npm run dev</code>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SetupGuide;
