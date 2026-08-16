import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Users,
  CheckCircle2,
  Mail,
  MousePointerClick,
  FileCheck,
  Award,
  Sparkles,
  ArrowUpRight,
  Download,
  Calendar,
  Layers
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  Cell
} from 'recharts';
import {
  ANALYTICS_FUNNEL_DATA,
  CAMPAIGN_PERFORMANCE_MONTHLY,
  SEGMENT_CONVERSION_DATA,
  PRODUCT_PERFORMANCE_DATA
} from '../data/mockData';

export default function Analytics({ onNavigateCampaigns }) {
  const [timeRange, setTimeRange] = useState('YTD 2026');

  const funnelMetrics = [
    { label: 'Audience Reach', value: '8,120', raw: 8120, rate: '100%', icon: Users, color: 'blue' },
    { label: 'Delivered', value: '7,984', raw: 7984, rate: '98.3%', icon: Mail, color: 'indigo' },
    { label: 'Opened', value: '5,420', raw: 5420, rate: '67.9%', icon: CheckCircle2, color: 'purple' },
    { label: 'Clicked CTA', value: '2,130', raw: 2130, rate: '39.3%', icon: MousePointerClick, color: 'purple' },
    { label: 'Applications', value: '482', raw: 482, rate: '22.6%', icon: FileCheck, color: 'amber' },
    { label: 'Conversions', value: '218', raw: 218, rate: '45.2%', icon: Award, color: 'emerald' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Marketing Performance & Attribution Intelligence
            </h2>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
              Live Pipeline
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Tracking customer conversion funnel, segment benchmarks, and balance sheet revenue lift.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
          >
            <option>Last 30 Days</option>
            <option>Q3 2026</option>
            <option>YTD 2026</option>
          </select>

          <button
            onClick={onNavigateCampaigns}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer shadow-xs"
          >
            Launch New Campaign
          </button>
        </div>
      </div>

      {/* 6 Key Conversion Funnel Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {funnelMetrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div
              key={m.label}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-2 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  {m.label}
                </span>
                <Icon className="w-4 h-4 text-slate-400" />
              </div>

              <h4 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                {m.value}
              </h4>

              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100">
                <span className="text-slate-400 font-medium">Stage Yield</span>
                <span className="font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  {m.rate}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 2-Column: Funnel Visualization & Campaign Performance Over Time */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Conversion Funnel Bar Chart */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Conversion Funnel Progression</h3>
              <p className="text-xs text-slate-500">Audience reach to bottom-funnel account conversions</p>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              2.68% Overall Conversion
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={ANALYTICS_FUNNEL_DATA}
                layout="vertical"
                margin={{ top: 10, right: 40, left: 50, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis
                  dataKey="stage"
                  type="category"
                  tick={{ fontSize: 11, fill: '#334155', fontWeight: 600 }}
                  width={90}
                />
                <Tooltip
                  formatter={(value, name, item) => [
                    `${value.toLocaleString()} accounts (${item.payload.percentage})`,
                    'Audience Volume',
                  ]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={24}>
                  {ANALYTICS_FUNNEL_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center text-xs">
            <div className="p-2 bg-slate-50 rounded-lg">
              <span className="text-slate-400 text-[10px] block uppercase">Open Rate</span>
              <strong className="text-slate-800 font-bold">67.9%</strong>
            </div>
            <div className="p-2 bg-slate-50 rounded-lg">
              <span className="text-slate-400 text-[10px] block uppercase">Click-To-Open (CTOR)</span>
              <strong className="text-slate-800 font-bold">39.3%</strong>
            </div>
            <div className="p-2 bg-slate-50 rounded-lg">
              <span className="text-slate-400 text-[10px] block uppercase">App-to-Convert</span>
              <strong className="text-emerald-600 font-bold">45.2%</strong>
            </div>
          </div>
        </div>

        {/* Campaign Performance Over Time (Monthly Trends) */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Campaign Response Trends</h3>
              <p className="text-xs text-slate-500">Monthly offers sent vs. final conversions</p>
            </div>
            <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              Jan - Aug 2026
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={CAMPAIGN_PERFORMANCE_MONTHLY}
                margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorConverted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 11, fill: '#10b981' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                  }}
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="sent"
                  name="Offers Sent"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorSent)"
                />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="converted"
                  name="Conversions"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorConverted)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-blue-500 inline-block" /> Offers Sent (Left Axis)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500 inline-block" /> Conversions (Right Axis)
            </span>
          </div>
        </div>
      </div>

      {/* 2-Column: Segment Conversion & Product Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Segment Conversion Comparison */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Segment Conversion Comparison</h3>
              <p className="text-xs text-slate-500">Actual conversion rate (%) vs. baseline target (%)</p>
            </div>
            <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
              Frequent Travellers Highest (5.8%)
            </span>
          </div>

          <div className="h-68 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={SEGMENT_CONVERSION_DATA}
                margin={{ top: 10, right: 20, left: 0, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="segment"
                  tick={{ fontSize: 10, fill: '#475569' }}
                  interval={0}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(v) => `${v}%`}
                  domain={[0, 7]}
                />
                <Tooltip
                  formatter={(val, name) => [
                    `${val}%`,
                    name === 'rate' ? 'Actual Conversion' : 'Baseline Target',
                  ]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar
                  dataKey="rate"
                  name="Actual Conversion Rate"
                  fill="#7c3aed"
                  radius={[4, 4, 0, 0]}
                  barSize={20}
                />
                <Bar
                  dataKey="target"
                  name="Baseline Target"
                  fill="#cbd5e1"
                  radius={[4, 4, 0, 0]}
                  barSize={20}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Product Performance & Revenue Lift */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Product Performance & Revenue Lift</h3>
              <p className="text-xs text-slate-500">Cross-sell and upsell balance sheet impact</p>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              +$24.1M Total Portfolio Lift
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-2.5">Banking Product</th>
                  <th className="px-4 py-2.5">Offers Sent</th>
                  <th className="px-4 py-2.5">Conversions</th>
                  <th className="px-4 py-2.5">Conv. Rate</th>
                  <th className="px-4 py-2.5 text-right">Revenue Lift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {PRODUCT_PERFORMANCE_DATA.map((p) => (
                  <tr key={p.product} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {p.product}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {p.offersSent.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {p.conversions}
                    </td>
                    <td className="px-4 py-3 font-bold text-blue-600">
                      {p.conversionRate}%
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-emerald-600">
                      {p.revenueLift}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 flex items-center justify-between">
            <span>Model attribution calculation: Multi-touch Markov chain</span>
            <span className="font-semibold text-slate-800">Confidence 96.2%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
