import React, { useState } from 'react';
import {
  Users,
  PieChart as PieIcon,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Plane,
  CreditCard,
  BadgeDollarSign,
  Briefcase,
  AlertTriangle,
  ChevronRight,
  Filter,
  DollarSign,
  BarChart3,
  CheckCircle2,
  Send
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { CUSTOMER_SEGMENTS, CUSTOMERS_LIST } from '../data/mockData';

export default function Segments({ onSelectSegmentFilter, onSelectCustomer, onStartCampaign }) {
  const [selectedSegmentId, setSelectedSegmentId] = useState('seg-1');

  const selectedSegment =
    CUSTOMER_SEGMENTS.find((s) => s.id === selectedSegmentId) ||
    CUSTOMER_SEGMENTS[0];

  // Customers belonging to the selected segment
  const segmentCustomers = CUSTOMERS_LIST.filter(
    (c) => c.segment === selectedSegment.name
  );

  // Data for Recharts Bar Chart: Customer count vs Average Spending
  const performanceChartData = CUSTOMER_SEGMENTS.slice(0, 5).map((seg) => ({
    name: seg.name,
    customerCount: seg.count,
    avgSpending: seg.avgSpendingRaw,
    percentage: seg.percentage,
  }));

  const getProductIcon = (productName) => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Top Banner / Summary */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Behavioral Micro-Segments (5 Key Clusters)
            </h2>
            <span className="text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full">
              52,480 Total Profiles
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Dynamic clustering based on spend velocity, travel frequency, credit inquiries, and liquidity retention.
          </p>
        </div>

        <button
          onClick={() => onStartCampaign && onStartCampaign(selectedSegment.recommendedProduct, selectedSegment.name)}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer shrink-0"
        >
          <Sparkles className="w-4 h-4" />
          <span>Launch Campaign for {selectedSegment.name}</span>
        </button>
      </div>

      {/* 5 Segment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {CUSTOMER_SEGMENTS.slice(0, 5).map((seg) => {
          const isSelected = seg.id === selectedSegmentId;
          const Icon = getProductIcon(seg.recommendedProduct);

          return (
            <div
              key={seg.id}
              onClick={() => setSelectedSegmentId(seg.id)}
              className={`rounded-xl border p-4.5 cursor-pointer transition-all flex flex-col justify-between space-y-3 ${
                isSelected
                  ? 'bg-white border-blue-600 shadow-md ring-2 ring-blue-500/20'
                  : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-xs'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block mr-1.5 align-middle"
                    style={{ backgroundColor: seg.color }}
                  />
                  <h3 className="text-sm font-bold text-slate-900 inline-block align-middle">
                    {seg.name}
                  </h3>
                </div>
                <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                  {seg.percentage}%
                </span>
              </div>

              {/* Metric Values */}
              <div className="space-y-2 pt-1 border-t border-slate-100">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs text-slate-500">Customer Count</span>
                  <span className="text-sm font-extrabold text-slate-900">
                    {seg.count.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-baseline justify-between">
                  <span className="text-xs text-slate-500">Avg. Spending</span>
                  <span className="text-sm font-extrabold text-blue-700">
                    {seg.avgSpending}/mo
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-100 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                    Recommended Product
                  </span>
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-800">
                    <Icon className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate">{seg.recommendedProduct}</span>
                  </div>
                </div>

                <div className="p-2 bg-purple-50/70 border border-purple-100 rounded-lg text-[11px] text-purple-900 leading-snug">
                  <div className="flex items-center gap-1 font-bold text-purple-800 mb-0.5">
                    <Sparkles className="w-3 h-3 text-purple-600" />
                    <span>AI Opportunity</span>
                  </div>
                  {seg.aiOpportunity}
                </div>
              </div>

              {/* Selection footer */}
              <div className="pt-1 flex items-center justify-between text-xs">
                <span
                  className={`text-[11px] font-bold ${
                    isSelected ? 'text-blue-600' : 'text-slate-400'
                  }`}
                >
                  {isSelected ? '● Currently Active' : 'Click to inspect'}
                </span>
                <ChevronRight className={`w-3.5 h-3.5 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Segment Performance Recharts Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Segment Performance & Spending Velocity
            </h3>
            <p className="text-xs text-slate-500">
              Comparison of customer base volume vs. monthly transactional value ($)
            </p>
          </div>
          <div className="flex items-center space-x-4 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-blue-600 inline-block" />
              Customer Volume
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
              Avg Spend ($)
            </span>
          </div>
        </div>

        <div className="h-68 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={performanceChartData}
              margin={{ top: 10, right: 30, left: 10, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#475569' }}
                interval={0}
              />
              <YAxis
                yAxisId="left"
                orientation="left"
                stroke="#2563eb"
                tick={{ fontSize: 11, fill: '#2563eb' }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#10b981"
                tick={{ fontSize: 11, fill: '#10b981' }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                }}
                formatter={(val, name) => [
                  name === 'customerCount' ? `${val.toLocaleString()} accounts` : `$${val.toLocaleString()}/mo`,
                  name === 'customerCount' ? 'Customer Size' : 'Avg Spend',
                ]}
              />
              <Bar
                yAxisId="left"
                dataKey="customerCount"
                fill="#2563eb"
                radius={[4, 4, 0, 0]}
                barSize={28}
              />
              <Bar
                yAxisId="right"
                dataKey="avgSpending"
                fill="#10b981"
                radius={[4, 4, 0, 0]}
                barSize={28}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Selected Segment Customer Table Drill-Down */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-slate-50/50">
          <div>
            <div className="flex items-center space-x-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: selectedSegment.color }}
              />
              <h3 className="text-sm font-bold text-slate-900">
                {selectedSegment.name} — Customer Profiles ({segmentCustomers.length} Sample Profiles)
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {selectedSegment.description}
            </p>
          </div>

          <div className="flex items-center space-x-2.5 self-start sm:self-auto">
            <button
              onClick={() => onSelectSegmentFilter && onSelectSegmentFilter(selectedSegment.name)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
            >
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <span>Filter in Customers Tab</span>
            </button>
            <button
              onClick={() => onStartCampaign && onStartCampaign(selectedSegment.recommendedProduct, selectedSegment.name)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors cursor-pointer shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Launch Campaign</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Monthly Spend</th>
                <th className="px-5 py-3">Recommended Product</th>
                <th className="px-5 py-3">Propensity</th>
                <th className="px-5 py-3">Primary Trigger Pattern</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {segmentCustomers.map((customer) => {
                const Icon = getProductIcon(customer.recommendedProduct);
                return (
                  <tr
                    key={customer.id}
                    className="hover:bg-slate-50/80 transition-colors"
                  >
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-700">
                          {customer.name.slice(0, 2)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{customer.name}</p>
                          <p className="text-[11px] text-slate-500">{customer.id} • {customer.city}</p>
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap font-bold text-slate-800">
                      {customer.monthlySpending}
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5 font-semibold text-slate-800">
                        <Icon className="w-3.5 h-3.5 text-blue-600" />
                        <span>{customer.recommendedProduct}</span>
                      </div>
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {customer.propensity}% Match
                      </span>
                    </td>

                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-600">
                      {customer.behaviourPatterns[0]}
                    </td>

                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      <button
                        onClick={() => onSelectCustomer(customer)}
                        className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg transition-colors cursor-pointer"
                      >
                        View 360°
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
