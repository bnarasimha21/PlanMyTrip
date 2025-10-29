import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface AdminStats {
  total_users: number;
  admin_users: number;
  total_trips: number;
  monthly_trips: number;
  subscriptions: {
    freemium: number;
    premium: number;
  };
  top_users?: {
    freemium: Array<{ name: string; email: string; user_id: string; trips: number }>;
    premium: Array<{ name: string; email: string; user_id: string; trips: number }>;
  };
  recent_trips?: Array<{ id: number; user_id: string; name: string; email: string; city: string; created_at: string }>;
  power_users_month?: Array<{ name: string; email: string; user_id: string; trips: number }>;
  top_cities_month?: Array<{ city: string; trips: number }>;
  trips_per_day_14?: Record<string, number>;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = (import.meta as any).env.VITE_API_BASE || window.location.origin;

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const resp = await fetch(`${API_BASE}/admin/stats`);
        const data = await resp.json();
        if (data.success) {
          setStats(data.stats as AdminStats);
        } else {
          setError(data.error || 'Failed to load stats');
        }
      } catch (e) {
        setError('Failed to load stats');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [API_BASE]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 text-slate-800">
      {/* Header */}
      <div className="bg-white/90 backdrop-blur-md border-b border-blue-200 shadow-lg relative z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link to="/" className="inline-block group">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">
                ✈️ TripXplorer Admin
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

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        {loading ? (
          <div className="text-center text-slate-600">Loading stats...</div>
        ) : error ? (
          <div className="text-center text-red-600">{error}</div>
        ) : stats ? (
          <>
            {/* KPI Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Total Users</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.total_users}</div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Admin Users</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.admin_users}</div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Total Trips</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.total_trips}</div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Trips This Month</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.monthly_trips}</div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Active Freemium</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.subscriptions.freemium}</div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <div className="text-sm text-slate-500">Active Premium</div>
                <div className="text-3xl font-bold text-slate-800 mt-1">{stats.subscriptions.premium}</div>
              </div>
            </div>

            {/* Top users */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Top 10 Freemium Users</h3>
                <div className="space-y-2">
                  {stats.top_users?.freemium?.length ? (
                    stats.top_users.freemium.map((u, idx) => (
                      <div key={u.user_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-semibold">{idx+1}</div>
                          <div>
                            <div className="text-slate-800 font-medium">{u.name || 'Unknown'}</div>
                            <div className="text-xs text-slate-500">{u.email}</div>
                          </div>
                        </div>
                        <div className="text-sm text-slate-600">{u.trips} trips</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-slate-500">No data</div>
                  )}
                </div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Top 10 Premium Users</h3>
                <div className="space-y-2">
                  {stats.top_users?.premium?.length ? (
                    stats.top_users.premium.map((u, idx) => (
                      <div key={u.user_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-semibold">{idx+1}</div>
                          <div>
                            <div className="text-slate-800 font-medium">{u.name || 'Unknown'}</div>
                            <div className="text-xs text-slate-500">{u.email}</div>
                          </div>
                        </div>
                        <div className="text-sm text-slate-600">{u.trips} trips</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-slate-500">No data</div>
                  )}
                </div>
              </div>
            </div>

            {/* Recent activity */}
            <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity (Last 10 Trips)</h3>
              <div className="divide-y divide-blue-100">
                {stats.recent_trips?.length ? (
                  stats.recent_trips.map((t) => (
                    <div key={t.id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="text-slate-800 font-medium">{t.name || 'Unknown'}</div>
                        <div className="text-xs text-slate-500">{t.email}</div>
                      </div>
                      <div className="text-sm text-slate-600">{t.city}</div>
                      <div className="text-xs text-slate-500">{new Date(t.created_at).toLocaleString()}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-500 py-3">No recent trips</div>
                )}
              </div>
            </div>

            {/* Power Users This Month */}
            {stats.power_users_month && stats.power_users_month.length > 0 && (
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Power Users (This Month)</h3>
                <div className="space-y-2">
                  {stats.power_users_month.map((u, idx) => (
                    <div key={u.user_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-yellow-400 to-orange-500 text-white flex items-center justify-center text-sm font-semibold">{idx+1}</div>
                        <div>
                          <div className="text-slate-800 font-medium">{u.name || 'Unknown'}</div>
                          <div className="text-xs text-slate-500">{u.email}</div>
                        </div>
                      </div>
                      <div className="text-sm text-slate-600 font-semibold">{u.trips} trips</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Trends & Insights */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Trips per Day (Last 14 days)</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {stats.trips_per_day_14 && Object.keys(stats.trips_per_day_14).length > 0 ? (
                    (() => {
                      const tripsData = stats.trips_per_day_14;
                      const maxCount = Math.max(1, Math.max(...Object.values(tripsData).map(v => v as number)));
                      return Object.entries(tripsData).map(([date, count]) => (
                        <div key={date} className="flex items-center gap-3">
                          <div className="w-24 text-xs text-slate-500">{new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                          <div className="flex-1 bg-blue-100 rounded h-6 flex items-center">
                            <div className="bg-blue-500 h-6 rounded flex items-center justify-end pr-2" style={{ width: `${Math.min(100, ((count as number) / maxCount) * 100)}%` }}>
                              {(count as number) > 0 && <span className="text-xs text-white font-medium">{count as number}</span>}
                            </div>
                          </div>
                        </div>
                      ));
                    })()
                  ) : (
                    <div className="text-sm text-slate-500">No trips in the last 14 days</div>
                  )}
                </div>
              </div>
              <div className="bg-white/90 rounded-2xl p-6 border border-blue-200 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Top Cities (This Month)</h3>
                <div className="space-y-2">
                  {stats.top_cities_month && stats.top_cities_month.length > 0 ? (
                    stats.top_cities_month.map((c, idx) => (
                      <div key={c.city + idx} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-semibold">{idx+1}</div>
                          <div className="text-slate-800 font-medium">{c.city}</div>
                        </div>
                        <div className="text-sm text-slate-600 font-semibold">{c.trips} trips</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-slate-500">No trips this month</div>
                  )}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

export default AdminDashboard;
