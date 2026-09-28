import React from 'react';
import { NavLink } from 'react-router-dom';
import { Layers, Building2, LayoutDashboard, FileText } from 'lucide-react';

export function Header() {
  const navLinkClass = ({ isActive }) =>
    `inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
      isActive
        ? 'bg-sky-50 text-sky-700'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <NavLink to="/" className="flex items-center space-x-3">
            <div className="bg-sky-600 p-2 rounded-lg text-white shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900">Billing 2.0</span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 border border-sky-200">
                Step 5 (OCR)
              </span>
            </div>
          </NavLink>

          <nav className="flex items-center space-x-2">
            <NavLink to="/" className={navLinkClass}>
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </NavLink>
            <NavLink to="/companies" className={navLinkClass}>
              <Building2 className="w-4 h-4" />
              Companies
            </NavLink>
            <NavLink to="/duty-slips" className={navLinkClass}>
              <FileText className="w-4 h-4" />
              Duty Slips
            </NavLink>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <span className="text-sm text-slate-500">System Ready</span>
        </div>
      </div>
    </header>
  );
}
