import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '../common/Header';

export function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        Billing 2.0 • Foundation Initialized
      </footer>
    </div>
  );
}
