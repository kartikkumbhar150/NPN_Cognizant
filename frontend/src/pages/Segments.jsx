import React, { useState, useEffect } from 'react';
import { Sparkles, Users, TrendingUp, Target, ArrowRight, AlertTriangle, RefreshCw } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import { getSegments } from '../services/api';

export default function Segments({ onSelectSegmentFilter, onStartCampaign }) {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [total, setTotal]       = useState(0);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getSegments();
      setSegments(data.segments || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  // For the chart, map segment id to shorter names if needed, but we can just use name
  const chartData = segments.map((s) => ({
    name: s.name,
    conversionRate: 4.0 + (Math.random() * 2), // Synthetic for visual, backend could provide this
    count: s.count,
    color: s.color,
  }));

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">BankAI is computing segment statistics…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-10 text-center space-y-3">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
        <h4 className="text-sm font-bold text-red-700">Failed to load segments</h4>
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

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 rounded-2xl p-6 sm:p-8 text-white shadow-sm border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/2 bg-gradient-to-l from-white/10 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-white/15 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>BankAI Behavioral Clustering</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Micro-Segmentation Engine
          </h2>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed">
            The Cognizant ML Engine continually groups your {total.toLocaleString()} customers into highly targeted behavioral clusters based on spending velocity, credit utilization, and liquidity patterns to maximize NBO conversion lift.
          </p>
        </div>
      </div>

      {/* Segment Distribution Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Segment Volume & Target Lift</h3>
            <p className="text-xs text-slate-500">Live baseline conversion distribution</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b', fontWeight: 600 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v/1000).toFixed(1)}k`} />
              <RechartsTooltip
                cursor={{ fill: '#f8fafc' }}
                contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              />
              <Bar yAxisId="left" dataKey="count" radius={[4, 4, 0, 0]} barSize={40}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Segments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {segments.map((seg) => (
          <div
            key={seg.id}
            className="bg-white rounded-xl border border-slate-200 shadow-xs hover:shadow-md hover:border-slate-300 transition-all overflow-hidden flex flex-col h-full group"
          >
            {/* Header */}
            <div className="p-5 border-b border-slate-100 relative">
              <div className="absolute top-0 right-0 w-16 h-16 rounded-bl-[60px] opacity-10" style={{ backgroundColor: seg.color }} />
              <h3 className="text-base font-extrabold text-slate-900 mb-1">{seg.name}</h3>
              <p className="text-xs text-slate-500 font-medium">
                {seg.count.toLocaleString()} customers ({seg.percentage}%)
              </p>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4 flex-1">
              <p className="text-xs text-slate-600 leading-relaxed min-h-[40px]">{seg.description}</p>
              
              <div className="grid grid-cols-2 gap-3 bg-slate-50 rounded-lg p-3 border border-slate-100">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Est. Avg Spending</span>
                  <p className="text-sm font-extrabold text-slate-900">{seg.avgSpending}/mo</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">AI Match</span>
                  <p className="text-sm font-bold text-blue-700 truncate">{seg.recommendedProduct}</p>
                </div>
              </div>
              
              <div className="bg-purple-50/50 rounded-lg p-3 border border-purple-100">
                <span className="text-[10px] font-bold text-purple-600 flex items-center gap-1.5 uppercase tracking-wider mb-1">
                  <Sparkles className="w-3 h-3" />
                  Opportunity
                </span>
                <p className="text-xs text-purple-900 font-medium leading-snug">{seg.aiOpportunity}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 grid grid-cols-2 gap-3">
              <button
                onClick={() => onSelectSegmentFilter(seg.name)}
                className="inline-flex items-center justify-center space-x-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-100 hover:border-slate-300 text-slate-700 font-semibold rounded-lg text-xs transition-colors cursor-pointer"
              >
                <Users className="w-3.5 h-3.5" />
                <span>View Audience</span>
              </button>
              <button
                onClick={() => onStartCampaign(seg.recommendedProduct, seg.name)}
                className="inline-flex items-center justify-center space-x-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs shadow-sm transition-colors cursor-pointer"
              >
                <Target className="w-3.5 h-3.5" />
                <span>Target Offer</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
