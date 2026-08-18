import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, PlusCircle } from 'lucide-react';

const PAGE_META = {
  '/': {
    title: 'Marketing Intelligence Dashboard',
    subtitle: '',
  },
  '/customers': {
    title: 'Customer Directory & Propensity',
    subtitle: 'Search, filter, and inspect bank customers with AI recommendation scores',
  },
  '/customers/360': {
    title: 'Customer 360° Profile',
    subtitle: 'In-depth transaction telemetry, behavioral patterns & personalized offer triggers',
  },
  '/segments': {
    title: 'Customer Segments & Opportunity Matrix',
    subtitle: 'Behavioral micro-clusters, average spending velocity & conversion metrics',
  },
  '/campaigns': {
    title: 'AI Campaign Orchestrator',
    subtitle: '5-Step campaign wizard with contextual AI copy generation and multi-channel preview',
  },
  '/campaigns/analytics': {
    title: 'Campaign Analytics',
    subtitle: 'Real-time performance, conversions and revenue lift for this campaign',
  },
  '/analytics': {
    title: 'Marketing Performance & Conversion Funnel',
    subtitle: 'Comprehensive attribution metrics, channel conversions and product revenue lift',
  },
};

export default function Header({ onOpenMobileMenu }) {
  const navigate = useNavigate();
  const location = useLocation();

  const meta = PAGE_META[location.pathname] || {
    title: 'Prism Platform',
    subtitle: 'Enterprise Marketing Intelligence',
  };

  const isCampaigns = location.pathname === '/campaigns';

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
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              {meta.subtitle}
            </p>
          </div>
        </div>

        {/* Right Side: Actions */}
        <div className="flex items-center space-x-2.5 sm:space-x-3 self-end md:self-auto">
          {!isCampaigns && (
            <button
              onClick={() => navigate('/campaigns')}
              className="inline-flex items-center space-x-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition-colors cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Campaign</span>
            </button>
          )}

          {isCampaigns && (
            <button
              onClick={() => navigate('/')}
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
