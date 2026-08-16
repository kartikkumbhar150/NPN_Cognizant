import React from 'react';
import { Sparkles, Menu, PlusCircle, Bell, Search, TrendingUp } from 'lucide-react';

export default function Header({ currentTab, onNavigate, onOpenMobileMenu }) {
  const getPageMeta = (tab) => {
    switch (tab) {
      case 'dashboard':
        return {
          title: 'Marketing Intelligence Dashboard',
          subtitle: 'Real-time customer segmentation, AI opportunities & next best offers',
        };
      case 'customers':
        return {
          title: 'Customer Directory & Propensity',
          subtitle: 'Search, filter, and inspect bank customers with AI recommendation scores',
        };
      case 'customer360':
        return {
          title: 'Customer 360° Profile',
          subtitle: 'In-depth transaction telemetry, behavioral patterns & personalized offer triggers',
        };
      case 'segments':
        return {
          title: 'Customer Segments & Opportunity Matrix',
          subtitle: 'Behavioral micro-clusters, average spending velocity & conversion metrics',
        };
      case 'campaigns':
        return {
          title: 'AI Campaign Orchestrator',
          subtitle: '5-Step campaign wizard with contextual AI copy generation and multi-channel preview',
        };
      case 'analytics':
        return {
          title: 'Marketing Performance & Conversion Funnel',
          subtitle: 'Comprehensive attribution metrics, channel conversions and product revenue lift',
        };
      default:
        return {
          title: 'BankAI Platform',
          subtitle: 'Enterprise Marketing Intelligence',
        };
    }
  };

  const meta = getPageMeta(currentTab);

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-xs border-b border-slate-200">
      <div className="px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left Side: Mobile Toggle & Page Title */}
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="p-2 -ml-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg lg:hidden"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                {meta.title}
              </h1>
              {currentTab === 'dashboard' && (
                <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-full">
                  <Sparkles className="w-3 h-3 text-purple-600" />
                  AI Engine Live
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              {meta.subtitle}
            </p>
          </div>
        </div>

        {/* Right Side: Quick Action & Live Metric */}
        <div className="flex items-center space-x-2.5 sm:space-x-3 self-end md:self-auto">
          {/* Quick AI status pill */}
          <div className="hidden lg:flex items-center space-x-2 bg-slate-50 border border-slate-200/80 px-3 py-1.5 rounded-lg text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-slate-600 font-medium">Model Precision:</span>
            <span className="font-bold text-slate-900">94.8%</span>
          </div>

          {/* Create Campaign CTA (only show when not already on campaign wizard step) */}
          {currentTab !== 'campaigns' && (
            <button
              onClick={() => onNavigate('campaigns')}
              className="inline-flex items-center space-x-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition-colors cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Campaign</span>
            </button>
          )}

          {currentTab === 'campaigns' && (
            <button
              onClick={() => onNavigate('dashboard')}
              className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs sm:text-sm font-medium transition-colors cursor-pointer"
            >
              <span>Back to Dashboard</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
