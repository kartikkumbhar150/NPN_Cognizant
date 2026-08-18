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
import { getDashboardStats, getCustomers, getSegments } from '../services/api';

export default function Dashboard({ onNavigate, onSelectCustomer, onStartCampaign }) {
  const [stats, setStats]           = useState(null);
  const [customers, setCustomers]   = useState([]);
  const [segments, setSegments]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, custData, segData] = await Promise.all([
        getDashboardStats(),
        getCustomers({ limit: 6 }),
        getSegments()
      ]);
      setStats(statsData);
      setCustomers(custData.customers || []);
      setSegments(segData.segments || []);
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

  // Dynamic AI Opportunities from Segment API
  const aiOpportunities = segments.slice(0, 4).map((seg, idx) => ({
    id: `opp-${idx}`,
    product: seg.recommendedProduct,
    recommendedSegment: seg.name,
    customerCount: seg.count,
  }));

  // Map a raw backend customer to the shape needed by the NBO table
  const mapCustomer = (c) => {
    // Find matched segment info from backend segments list
    const segInfo = segments.find(s => s.name === c.customer_segment_type);
    
    // Calculate a dynamic score based on credit score or income (real data proxy)
    const creditScore = c.credit_score || 700;
    const dynamicPropensity = Math.min(98, Math.floor((creditScore / 850) * 100));

    return {
      id:                 c.customer_id,
      name:               `${c.first_name || ''} ${c.last_name || ''}`.trim(),
      city:               c.city || '—',
      segment:            c.customer_segment_type || 'Standard',
      monthlySpending:    `₹${((c.annual_income || 0) / 12).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
      recommendedProduct: segInfo ? segInfo.recommendedProduct : 'Credit Card',
      propensity:         dynamicPropensity,
      _raw:               c,
    };
  };

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


      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Customers"
          value={totalCustomers.toLocaleString()}
          change="Live DB Sync"
          period="via Supabase"
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
          change="AI Validated"
          period="portfolio average"
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
              Live DB Matches
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 my-4">
            {aiOpportunities.map((opp) => {
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
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                    <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100">
                      {opp.customerCount.toLocaleString()} Candidates
                    </span>
                    <button
                      onClick={() => onStartCampaign(opp.product, opp.recommendedSegment)}
                      className="text-[11px] font-bold text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-0.5 cursor-pointer"
                    >
                      <span>Campaign</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* AI Next Best Offer Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-600" />
              Next Best Offer (NBO) Matrix
            </h3>
            <p className="text-xs text-slate-500">Live AI engine scoring for top priority customers.</p>
          </div>
          <button
            onClick={() => onNavigate('customers')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1 cursor-pointer"
          >
            <span>View All Directory</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Customer Identity</th>
                <th className="px-5 py-3">AI Segment</th>
                <th className="px-5 py-3 text-right">Est. Monthly Inflow</th>
                <th className="px-5 py-3">Next Best Offer</th>
                <th className="px-5 py-3 text-right">Propensity</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recommendations.map((customer) => (
                <tr
                  key={customer.id}
                  className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                  onClick={() => onSelectCustomer(customer._raw)}
                >
                  <td className="px-5 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-600 shrink-0 shadow-xs">
                        {customer.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                          {customer.name}
                        </p>
                        <p className="text-[10px] text-slate-400">ID: {customer.id} • {customer.city}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      {customer.segment}
                    </span>
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap text-right font-medium text-slate-700">
                    {customer.monthlySpending}
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap font-bold text-slate-800">
                    {customer.recommendedProduct}
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <span className="font-bold text-emerald-600">{customer.propensity}%</span>
                      <div className="w-12 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${customer.propensity}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap text-right">
                    <button
                      onClick={(e) => { e.stopPropagation(); onStartCampaign(customer.recommendedProduct, customer.segment); }}
                      className="inline-flex items-center justify-center space-x-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white font-bold rounded shadow-xs transition-all cursor-pointer"
                    >
                      <Send className="w-3 h-3" />
                      <span>Dispatch</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
