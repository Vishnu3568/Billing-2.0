import React, { useEffect, useState } from 'react';
import { healthService } from '../api/client';
import { CheckCircle2, AlertCircle, RefreshCw, Server, Database, HardDrive, ShieldCheck } from 'lucide-react';

export function Dashboard() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthService.checkHealth();
      setHealth(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend API');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Status</h1>
            <p className="text-sm text-slate-500 mt-1">
              Billing 2.0 application foundation is active. Business logic and modules will be enabled in subsequent steps.
            </p>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend API Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-3 bg-sky-50 text-sky-600 rounded-lg">
            <Server className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">FastAPI Backend</p>
            <div className="mt-1 flex items-center gap-2">
              {loading ? (
                <span className="text-sm text-slate-400">Checking...</span>
              ) : health?.status === 'ok' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-sm font-semibold text-slate-800">Online ({health.version})</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-rose-500" />
                  <span className="text-sm font-semibold text-rose-600">Offline</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">MongoDB</p>
            <div className="mt-1 flex items-center gap-2">
              {loading ? (
                <span className="text-sm text-slate-400">Checking...</span>
              ) : health?.database_connected ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-sm font-semibold text-slate-800">Connected</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                  <span className="text-sm font-semibold text-amber-600">Not Connected</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Storage Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <HardDrive className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Storage Layer</p>
            <div className="mt-1 flex items-center gap-2">
              {health?.storage_type ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-sm font-semibold text-slate-800">
                    {health.storage_type.toUpperCase()} Storage
                  </span>
                </>
              ) : (
                <span className="text-sm text-slate-400">Ready</span>
              )}
            </div>
          </div>
        </div>

        {/* Auth Module */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Authentication</p>
            <div className="mt-1">
              <span className="text-sm font-semibold text-slate-800">JWT Scaffolding</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-rose-700">
            <p className="font-semibold">Backend Connection Issue</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900 mb-3">Foundation Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-600">
          <div className="space-y-2 p-4 bg-slate-50 rounded-lg border border-slate-100">
            <h3 className="font-medium text-slate-800">Frontend Stack</h3>
            <ul className="list-disc list-inside space-y-1 text-slate-600 text-xs">
              <li>React 18 + Vite</li>
              <li>Tailwind CSS</li>
              <li>React Router v6</li>
              <li>Centralized API Client layer</li>
            </ul>
          </div>
          <div className="space-y-2 p-4 bg-slate-50 rounded-lg border border-slate-100">
            <h3 className="font-medium text-slate-800">Backend Stack</h3>
            <ul className="list-disc list-inside space-y-1 text-slate-600 text-xs">
              <li>FastAPI + Uvicorn</li>
              <li>MongoDB + PyMongo Connection Manager</li>
              <li>Storage Service Abstraction (Local/Cloud ready)</li>
              <li>Pydantic Schemas & Settings</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
