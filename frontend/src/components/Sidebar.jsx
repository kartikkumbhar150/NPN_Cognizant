import React from 'react';
import {
  LayoutDashboard,
  Users,
  PieChart,
  Megaphone,
  BarChart3,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  Zap,
  Award
} from 'lucide-react';

export default function Sidebar({ currentTab, onSelectTab, isMobileOpen, setIsMobileOpen }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'customers', label: 'Customers', icon: Users, badge: '52.4k' },
    { id: 'segments', label: 'Segments', icon: PieChart, badge: '5' },
    { id: 'campaigns', label: 'Campaigns', icon: Megaphone, badge: '18 Active' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
  ];

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
        <div className="h-18 px-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">Bank</span>
                <span className="text-xl font-extrabold tracking-tight text-blue-600">AI</span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-purple-100 text-purple-700 rounded">v2.4</span>
              </div>
              <p className="text-[11px] font-medium text-slate-500 tracking-tight">Marketing Intelligence</p>
            </div>
          </div>
        </div>

        {/* Hackathon Project Tag */}
        <div className="px-4 pt-3 pb-1">
          <div className="flex items-center space-x-2 px-3 py-2 bg-slate-50 border border-slate-100 rounded-lg text-xs text-slate-600">
            <Award className="w-4 h-4 text-blue-600 shrink-0" />
            <div className="truncate">
              <span className="font-semibold text-slate-800">Cognizant Hackathon</span>
              <p className="text-[10px] text-slate-400">Enterprise AI Track</p>
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
            const isActive = currentTab === item.id || (currentTab === 'customer360' && item.id === 'customers');

            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  if (setIsMobileOpen) setIsMobileOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs border border-blue-100/70'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>

                <div className="flex items-center space-x-1.5">
                  {item.badge && (
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-blue-500" />}
                </div>
              </button>
            );
          })}
        </div>

        {/* AI Engine Status Card */}
        <div className="p-4 border-t border-slate-100">
          <div className="p-3 bg-gradient-to-br from-purple-50/80 via-slate-50 to-blue-50/60 border border-purple-100 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs font-bold text-slate-800">Propensity Engine</span>
              </div>
              <span className="text-[10px] font-semibold text-purple-700 bg-purple-100/80 px-1.5 py-0.5 rounded">Active</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Evaluating 52,480 profiles with 91% top confidence scoring.
            </p>
            <div className="flex items-center justify-between text-[11px] text-slate-600 pt-1 border-t border-purple-100/60">
              <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> Latency</span>
              <span className="font-semibold text-slate-800">14ms</span>
            </div>
          </div>
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
