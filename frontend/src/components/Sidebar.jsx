import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  PieChart,
  Megaphone,
  BarChart3,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { path: '/customers', label: 'Customers', icon: Users },
  { path: '/segments', label: 'Segments', icon: PieChart },
  { path: '/campaigns', label: 'Campaigns', icon: Megaphone },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Sidebar({ onSelectTab, isMobileOpen, setIsMobileOpen }) {
  const navigate = useNavigate();

  return (
    <>
      {/* Mobile backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-40 lg:hidden backdrop-blur-xs"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div
          className="h-18 px-5 border-b border-slate-100 flex items-center justify-between cursor-pointer"
          onClick={() => navigate('/')}
        >
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="Prism Logo" className="w-10 h-10 object-contain" />
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">Prism</span>
              </div>
              <p className="text-[11px] font-medium text-slate-500 tracking-tight">Marketing Intelligence</p>
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <div className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
          <div className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Main Navigation
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                onClick={() => { if (setIsMobileOpen) setIsMobileOpen(false); }}
                className={({ isActive }) =>
                  `w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs border border-blue-100/70'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center space-x-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {isActive && <ChevronRight className="w-3.5 h-3.5 text-blue-500" />}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Footer User Profile */}
        <div className="p-3.5 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
              MK
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-800 truncate">Marketing Director</p>
              <p className="text-[11px] text-slate-500 truncate">Retail Banking Division</p>
            </div>
          </div>
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" title="Enterprise Secure" />
        </div>
      </aside>
    </>
  );
}
