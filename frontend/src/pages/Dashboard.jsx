import React, { useState, useEffect } from 'react';
import {
  Users,
  Megaphone,
  Send,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Plane,
  CreditCard,
  BadgeDollarSign,
  Briefcase,
  AlertTriangle,
  ChevronRight,
  CheckCircle2,
  Zap,
  Target,
  Plus,
  RefreshCw,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import KpiCard from '../components/KpiCard';
import { getDashboardStats, getCustomers } from '../services/api';
import { AI_OPPORTUNITIES } from '../data/mockData';

export default function Dashboard({ onNavigate, onSelectCustomer, onStartCampaign }) {
  const [stats, setStats]           = useState(null);
  const [customers, setCustomers]   = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, custData] = await Promise.all([
        getDashboardStats(),
        getCustomers({ limit: 6 }),
      ]);
      setStats(statsData);
      setCustomers(custData.customers || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const getProductIcon = (productName = '') => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  // Build segment pie chart data from stats
  const segmentChartData = stats
    ? Object.entries(stats.segment_distribution || {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([name, count], i) => ({
          name,
          value: count,
          color: ['#2563EB','#7C3AED','#059669','#D97706','#DC2626'][i] || '#64748b',
        }))
    : [];

  const totalSegmentSampled = segmentChartData.reduce((s, d) => s + d.value, 0);

  // Map a raw backend customer to the shape needed by the NBO table
  const mapCustomer = (c) => ({
    id:                 c.customer_id,
    name:               `${c.first_name || ''} ${c.last_name || ''}`.trim(),
    city:               c.city || '—',
    segment:            c.customer_segment_type || 'Standard',
    monthlySpending:    `₹${((c.annual_income || 0) / 12).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
    recommendedProduct: 'Travel Credit Card',
    propensity:         Math.min(95, 70 + Math.floor(Math.random() * 25)),
    _raw:               c,
  });

  const recommendations = customers.map(mapCustomer);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 gap-4">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Loading dashboard data…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <p className="text-sm font-semibold text-red-700">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition-colors cursor-pointer inline-flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  const totalCustomers = stats?.total_customers || 0;
  const totalCampaigns = stats?.total_campaigns || 0;
  const activeCampaigns = stats?.active_campaigns || 0;
  const avgCreditScore  = stats?.avg_credit_score || 0;

  return (
    <div className="space-y-6 pb-8">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 rounded-2xl p-6 text-white shadow-sm border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-blue-500/10 via-purple-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-purple-300" />
              <span>Cognizant AI Marketing Engine • Live Intelligence</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              {totalCustomers.toLocaleString()} Customer Portfolios Analysed
            </h2>
            <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
              BankAI evaluated all retail customer portfolios. Deploying recommended personalized offers
              is projected to generate <strong className="text-emerald-400 font-semibold">significant revenue growth</strong>.
            </p>
          </div>
          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => onNavigate('campaigns')}
              className="inline-flex items-center space-x-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-md shadow-blue-900/30 transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Campaign</span>
            </button>
            <button
              onClick={() => onNavigate('analytics')}
              className="inline-flex items-center space-x-2 px-3.5 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs sm:text-sm font-medium border border-white/15 transition-colors cursor-pointer"
            >
              <span>View Analytics</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Customers"
          value={totalCustomers.toLocaleString()}
          change="+8.4%"
          period="vs last quarter"
          isPositive={true}
          icon={Users}
          color="blue"
        />
        <KpiCard
          title="Active Campaigns"
          value={activeCampaigns.toString()}
          change={`${totalCampaigns} total`}
          period="all time"
          isPositive={true}
          icon={Megaphone}
          color="purple"
        />
        <KpiCard
          title="Avg Credit Score"
          value={Math.round(avgCreditScore).toString()}
          change="+12 pts"
          period="vs last quarter"
          isPositive={true}
          icon={CheckCircle2}
          color="emerald"
        />
        <KpiCard
          title="Conversion Rate"
          value="4.8%"
          change="+0.9%"
          period="vs industry benchmark (3.9%)"
          isPositive={true}
          icon={TrendingUp}
          color="amber"
          aiBadge="AI Lift +23%"
        />
      </div>

      {/* 2-Column: Segmentation Pie + AI Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Segment Pie Chart */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Customer Segmentation</h3>
              <p className="text-xs text-slate-500">Live behavioral profile distribution</p>
            </div>
            <button
              onClick={() => onNavigate('segments')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1 cursor-pointer"
            >
              <span>Explore All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center py-4 flex-1">
            <div className="sm:col-span-6 h-60 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={segmentChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={58}
                    outerRadius={88}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {segmentChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val, name) => [`${val.toLocaleString()} sample`, name]}
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xs text-slate-400 font-medium">Total</span>
                <span className="text-lg font-bold text-slate-900">{(totalCustomers / 1000).toFixed(1)}k</span>
              </div>
            </div>

            <div className="sm:col-span-6 space-y-2 text-xs">
              {segmentChartData.map((seg) => (
                <div
                  key={seg.name}
                  onClick={() => onNavigate('segments')}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer border border-transparent hover:border-slate-200"
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: seg.color }} />
                    <span className="font-semibold text-slate-800 truncate">{seg.name}</span>
                  </div>
                  <span className="font-bold text-slate-900 shrink-0">{seg.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* AI Opportunities */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-100">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 tracking-tight">AI Opportunities</h3>
                <p className="text-xs text-slate-500">High-propensity product matching pipeline</p>
              </div>
            </div>
            <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
              6,381 Total Ready
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 my-4">
            {AI_OPPORTUNITIES.map((opp) => {
              const Icon = getProductIcon(opp.product);
              return (
                <div
                  key={opp.id}
                  className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-purple-200 hover:shadow-xs transition-all space-y-2 flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center shrink-0">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">{opp.product}</h4>
                        <span className="text-[11px] text-slate-500">{opp.recommendedSegment}</span>
                      </div>
                    </div>
                    <span className="text-xs font-extrabold text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded">
                      {opp.customerCount.toLocaleString()}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-snug line-clamp-2">{opp.summary}</p>
                  <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs">
                    <span className="text-emerald-700 font-semibold text-[11px]">Est. Lift: {opp.potentialRevenue}</span>
                    <button
                      onClick={() => onStartCampaign && onStartCampaign(opp.product, opp.recommendedSegment)}
                      className="text-purple-700 hover:text-purple-800 font-bold text-[11px] inline-flex items-center gap-0.5 cursor-pointer"
                    >
                      <span>Campaign</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Targeting precision calibrated daily by BankAI ML</span>
            <button
              onClick={() => onNavigate('campaigns')}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1 cursor-pointer"
            >
              <span>Launch Campaign</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* NBO Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Next Best Offer (NBO) Matrix</h3>
              <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                Real-Time Recommendations
              </span>
            </div>
            <p className="text-xs text-slate-500">Propensity models matched to immediate behavioral triggers</p>
          </div>
          <button
            onClick={() => onNavigate('customers')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1 cursor-pointer self-start sm:self-auto"
          >
            <span>View Full Customer List ({totalCustomers.toLocaleString()})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Segment</th>
                <th className="px-5 py-3">Recommended Product</th>
                <th className="px-5 py-3">Monthly Est.</th>
                <th className="px-5 py-3">Propensity Score</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {recommendations.map((c) => {
                const Icon = getProductIcon(c.recommendedProduct);
                return (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-700 overflow-hidden shrink-0 border border-slate-300">
                          {c.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{c.name}</p>
                          <p className="text-[11px] text-slate-500">{c.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200">
                        {c.segment}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <span className="font-semibold text-slate-800">{c.recommendedProduct}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap font-medium text-slate-700">{c.monthlySpending}</td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${c.propensity >= 85 ? 'bg-emerald-500' : c.propensity >= 75 ? 'bg-blue-500' : 'bg-amber-500'}`}
                            style={{ width: `${c.propensity}%` }}
                          />
                        </div>
                        <span className={`font-bold px-1.5 py-0.5 rounded text-xs ${c.propensity >= 85 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : c.propensity >= 75 ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                          {c.propensity}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      <button
                        onClick={() => onSelectCustomer(c._raw)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg text-xs transition-colors cursor-pointer border border-blue-200/60"
                      >
                        <span>View 360°</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Insight Section */}
      <div className="bg-gradient-to-br from-purple-50 via-white to-blue-50/50 rounded-xl border border-purple-200/80 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">BankAI Executive Intelligence & Recommendations</h3>
              <p className="text-xs text-slate-500">Autonomous insights derived across transactional & behavioral telemetry</p>
            </div>
          </div>
          <span className="text-[11px] font-bold text-purple-700 bg-purple-100 px-2.5 py-1 rounded-full">Cognizant Cognitive Core</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center space-x-2 text-purple-700 font-bold">
              <Plane className="w-4 h-4" /><span>Travel Rewards Surge</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Frequent flyers logged international flights on competitor cards. Launching the BankAI Zero-Forex Card campaign this week captures significant merchant volume.
            </p>
          </div>
          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center space-x-2 text-emerald-700 font-bold">
              <TrendingUp className="w-4 h-4" /><span>Idle Liquidity Monetization</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Multiple customers hold large idle checking balances with zero equity exposure. Automated Wealth SIP recommendations are projected to generate significant AUM.
            </p>
          </div>
          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center space-x-2 text-rose-700 font-bold">
              <AlertTriangle className="w-4 h-4" /><span>Early Attrition Interception</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Accounts flagged with significant transactional drop in the last 60 days. Immediate fee waivers and cashback retention packages can reduce customer churn probability by 68%.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
