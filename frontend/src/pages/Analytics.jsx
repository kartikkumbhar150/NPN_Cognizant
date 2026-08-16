import React, { useState, useEffect } from 'react';
import {
  BarChart2, TrendingUp, Users, Target, ArrowRight,
  Filter, Calendar, Download, Sparkles, Activity,
  ChevronRight, RefreshCw, AlertTriangle
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { getAnalytics } from '../services/api';

export default function Analytics({ onNavigateCampaigns }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getAnalytics();
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">BankAI is compiling telemetry data…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-10 text-center space-y-3">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
        <h4 className="text-sm font-bold text-red-700">Failed to load analytics</h4>
        <p className="text-xs text-red-600">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition-colors cursor-pointer inline-flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  const { funnel, monthly_performance, segment_conversion, product_performance, summary } = data;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner & Date Filter */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Marketing Analytics</h2>
          <p className="text-sm text-slate-500 mt-1">Live telemetry of AI-driven campaign performance and conversion attribution.</p>
        </div>
        <div className="flex items-center space-x-3 shrink-0">
          <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 flex items-center space-x-2 text-sm shadow-xs">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="font-semibold text-slate-700">Last 8 Months</span>
          </div>
          <button className="bg-white border border-slate-200 hover:bg-slate-50 rounded-lg p-2 text-slate-600 shadow-xs transition-colors cursor-pointer">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Output</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><BarChart2 className="w-4 h-4" /></div>
          </div>
          <h4 className="text-2xl font-extrabold text-slate-900">{summary.total_campaigns}</h4>
          <p className="text-xs text-slate-500">Active & completed campaigns</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Offers Dispatched</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center"><Users className="w-4 h-4" /></div>
          </div>
          <h4 className="text-2xl font-extrabold text-slate-900">{summary.total_offers_sent.toLocaleString()}</h4>
          <p className="text-xs text-slate-500">Personalized comms sent</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Conversion Rate</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center"><Target className="w-4 h-4" /></div>
          </div>
          <h4 className="text-2xl font-extrabold text-slate-900">{summary.avg_conversion_rate}%</h4>
          <p className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Lift vs industry (3.2%)
          </p>
        </div>

        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl border border-indigo-500 p-5 shadow-sm text-white space-y-1 relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 opacity-20"><Sparkles className="w-24 h-24" /></div>
          <div className="flex items-center justify-between mb-2 relative z-10">
            <span className="text-xs font-bold text-indigo-200 uppercase tracking-wider">Product Conversions</span>
            <div className="w-8 h-8 rounded-lg bg-white/20 text-white flex items-center justify-center"><Activity className="w-4 h-4" /></div>
          </div>
          <h4 className="text-2xl font-extrabold text-white relative z-10">{summary.total_conversions.toLocaleString()}</h4>
          <p className="text-xs text-indigo-100 relative z-10">New product acquisitions</p>
        </div>
      </div>

      {/* 2-Column: Funnel + Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Global Conversion Funnel */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col">
          <div className="pb-4 border-b border-slate-100 mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Aggregate Conversion Funnel</h3>
              <p className="text-xs text-slate-500">From audience selection to product origination</p>
            </div>
          </div>

          <div className="flex-1 flex flex-col justify-center space-y-3">
            {funnel.map((stage, i) => (
              <div key={stage.stage} className="relative group">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-slate-700">{stage.stage}</span>
                  <span className="font-semibold text-slate-900">{stage.count.toLocaleString()} <span className="text-slate-400">({stage.percentage})</span></span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden border border-slate-200/60">
                  <div
                    className="h-full rounded-full transition-all duration-1000 ease-out"
                    style={{
                      width: stage.percentage,
                      backgroundColor: stage.fill,
                      opacity: 1 - (i * 0.1)
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Temporal Performance Area Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-base font-bold text-slate-900">Campaign Execution Volume</h3>
            <p className="text-xs text-slate-500">Offers sent vs. conversions over the last 8 months</p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthly_performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v/1000}k`} />
                <RechartsTooltip
                  contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="sent" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorSent)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 2-Column: Segment Rates + Product Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Segment Conversion Benchmarks */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-base font-bold text-slate-900">Segment Conversion Lift</h3>
            <p className="text-xs text-slate-500">Actual vs baseline target</p>
          </div>
          
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segment_conversion} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" hide />
                <YAxis dataKey="segment" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#475569', fontWeight: 600 }} width={110} />
                <RechartsTooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '11px' }}
                />
                <Bar dataKey="rate" radius={[0, 4, 4, 0]} barSize={20}>
                  {segment_conversion.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.rate > entry.target ? '#10b981' : '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Product Performance Table */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Product Origination Performance</h3>
              <p className="text-xs text-slate-500">Revenue impact by target product</p>
            </div>
            <button
              onClick={onNavigateCampaigns}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1 cursor-pointer"
            >
              <span>Boost via New Campaign</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-3">Product Name</th>
                  <th className="px-5 py-3 text-right">Offers Sent</th>
                  <th className="px-5 py-3 text-right">Conversions</th>
                  <th className="px-5 py-3">Conv. Rate</th>
                  <th className="px-5 py-3">Est. Revenue Lift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {product_performance.map((item, i) => (
                  <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-bold text-slate-900">{item.product}</td>
                    <td className="px-5 py-3.5 font-medium text-slate-600 text-right">{item.offersSent.toLocaleString()}</td>
                    <td className="px-5 py-3.5 font-extrabold text-emerald-600 text-right">{item.conversions.toLocaleString()}</td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-700">{item.conversionRate}%</span>
                        <div className="w-12 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(item.conversionRate / 6) * 100}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-indigo-700 bg-indigo-50/50">
                      {item.revenueLift}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
