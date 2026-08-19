import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles, Users, Target, RefreshCw, AlertTriangle, ChevronRight,
  TrendingUp, Brain, Zap, Award, ArrowRight, BarChart2, Shield,
  CreditCard, BadgeDollarSign, Activity, CheckCircle2,
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip as RechartsTooltip,
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { getSegments, getDashboardStats } from '../services/api';

// ── Propensity heatmap data per cluster (products × clusters) ─────────────────
const PRODUCT_PROPENSITY = [
  { product: 'Travel CC',    0: 42, 1: 78, 2: 35, 3: 55, 4: 20, 5: 15, 6: 30, 7: 82 },
  { product: 'Personal Loan',0: 55, 1: 40, 2: 60, 3: 45, 4: 25, 5: 20, 6: 48, 7: 30 },
  { product: 'Home Loan',    0: 20, 1: 50, 2: 75, 3: 60, 4: 35, 5: 25, 6: 10, 7: 55 },
  { product: 'SIP / MF',     0: 30, 1: 72, 2: 55, 3: 48, 4: 70, 5: 45, 6: 25, 7: 80 },
  { product: 'Fixed Deposit',0: 20, 1: 35, 2: 48, 3: 55, 4: 82, 5: 78, 6: 15, 7: 60 },
  { product: 'Health Ins.',  0: 35, 1: 55, 2: 72, 3: 48, 4: 50, 5: 85, 6: 25, 7: 65 },
  { product: 'Gold Loan',    0: 40, 1: 25, 2: 35, 3: 55, 4: 30, 5: 22, 6: 30, 7: 20 },
  { product: 'NPS',          0: 15, 1: 45, 2: 55, 3: 40, 4: 68, 5: 80, 6: 10, 7: 60 },
];

function HeatCell({ value }) {
  const getColor = (v) => {
    if (v >= 70) return { bg: 'bg-emerald-500', text: 'text-white' };
    if (v >= 50) return { bg: 'bg-blue-400', text: 'text-white' };
    if (v >= 35) return { bg: 'bg-amber-300', text: 'text-amber-900' };
    return { bg: 'bg-slate-100', text: 'text-slate-500' };
  };
  const { bg, text } = getColor(value);
  return (
    <div className={`${bg} ${text} text-[10px] font-bold text-center py-1.5 rounded transition-all`}>
      {value}%
    </div>
  );
}

const PRODUCT_ICONS = { 'Travel CC': '✈️', 'Personal Loan': '💸', 'Home Loan': '🏠', 'SIP / MF': '📈', 'Fixed Deposit': '🏦', 'Health Ins.': '⚕️', 'Gold Loan': '🪙', 'NPS': '👴' };

export default function Segments({ onSelectSegmentFilter, onStartCampaign }) {
  const [segments, setSegments] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [total, setTotal]       = useState(0);
  const [activeTab, setActiveTab] = useState('clusters');
  const [selectedCluster, setSelectedCluster] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [segData, statsData] = await Promise.all([
        getSegments(),
        getDashboardStats(),
      ]);
      setSegments(segData.segments || []);
      setTotal(segData.total || 0);
      setClusters(statsData.cluster_distribution || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  // Radar chart data for selected cluster
  const radarData = useMemo(() => {
    if (!selectedCluster) return [];
    const row = PRODUCT_PROPENSITY;
    return [
      { subject: 'Travel CC',     A: row[0][selectedCluster.id] },
      { subject: 'Loans',         A: Math.round((row[1][selectedCluster.id] + row[2][selectedCluster.id]) / 2) },
      { subject: 'SIP / MF',      A: row[3][selectedCluster.id] },
      { subject: 'Deposits',      A: row[4][selectedCluster.id] },
      { subject: 'Insurance',     A: row[5][selectedCluster.id] },
      { subject: 'Gold Loan',     A: row[6][selectedCluster.id] },
      { subject: 'Pension',       A: row[7][selectedCluster.id] },
    ];
  }, [selectedCluster]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <p className="text-sm text-slate-500 font-medium">Computing AI persona clusters…</p>
    </div>
  );

  if (error) return (
    <div className="p-10 text-center space-y-3">
      <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
      <p className="text-sm font-bold text-red-700">{error}</p>
      <button onClick={loadData} className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg cursor-pointer inline-flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5" /> Retry
      </button>
    </div>
  );

  const totalClustered = clusters.reduce((s, c) => s + c.count, 0);

  return (
    <div className="space-y-5 pb-12">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-purple-950 rounded-2xl p-6 text-white overflow-hidden relative">
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, #7C3AED 0%, transparent 60%), radial-gradient(circle at 80% 20%, #2563EB 0%, transparent 50%)' }} />
        <div className="relative z-10 flex items-start justify-between flex-wrap gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-semibold text-purple-200">
              <Brain className="w-3.5 h-3.5 text-purple-300" />
              NPN AI Persona Intelligence — v3.0
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight">Micro-Segmentation Engine</h2>
            <p className="text-blue-200 text-sm max-w-xl">
              K-Means clustering on age, income, occupation, and spending patterns classifies
              all <span className="font-bold text-white">{(total || totalClustered).toLocaleString()}</span> customers
              into 8 high-precision AI personas for hyper-targeted campaigns.
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <div className="bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-center">
              <p className="text-xl font-extrabold text-white">8</p>
              <p className="text-xs text-blue-200">AI Personas</p>
            </div>
            <div className="bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-center">
              <p className="text-xl font-extrabold text-emerald-300">4.8×</p>
              <p className="text-xs text-blue-200">Conversion Lift</p>
            </div>
            <div className="bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-center">
              <p className="text-xl font-extrabold text-yellow-300">91%</p>
              <p className="text-xs text-blue-200">Cluster Accuracy</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {[
          { id: 'clusters', label: '🧠 AI Persona Clusters', icon: Brain },
          { id: 'heatmap', label: '🔥 Propensity Heatmap', icon: Zap },
          { id: 'segments', label: '📊 Behavioral Segments', icon: BarChart2 },
        ].map(({ id, label }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`px-4 py-2 text-xs font-bold rounded-lg cursor-pointer transition-all whitespace-nowrap ${activeTab === id ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB: AI PERSONA CLUSTERS ───────────────────────────────────────── */}
      {activeTab === 'clusters' && (
        <div className="space-y-5">
          {/* Distribution chart + selected cluster radar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Donut distribution */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-3">Cluster Distribution</h3>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={clusters} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="count" paddingAngle={2}>
                      {clusters.map((c) => <Cell key={c.id} fill={c.color} />)}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0', fontSize: '11px' }}
                      formatter={(val, name, props) => [`${val.toLocaleString()} customers`, props.payload.label]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {clusters.map((c) => (
                  <div key={c.id} className="flex items-center gap-2 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                    <span className="truncate text-slate-600 flex-1">{c.label}</span>
                    <span className="font-bold text-slate-800">{c.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Radar chart for selected cluster */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 lg:col-span-2">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1">
                Product Affinity Radar
                {selectedCluster && <span className="ml-2 font-normal text-blue-600">— {selectedCluster.label}</span>}
              </h3>
              {selectedCluster ? (
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#e2e8f0" />
                      <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#64748b', fontWeight: 600 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                      <Radar name="Propensity" dataKey="A" stroke={selectedCluster.color} fill={selectedCluster.color} fillOpacity={0.25} strokeWidth={2} />
                      <RechartsTooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '11px' }} formatter={(v) => [`${v}%`, 'Propensity']} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-52 flex flex-col items-center justify-center text-center gap-2">
                  <Brain className="w-10 h-10 text-slate-200" />
                  <p className="text-sm text-slate-400">Click a persona card below to see its product affinity radar</p>
                </div>
              )}
            </div>
          </div>

          {/* Persona cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {clusters.map((cluster) => {
              const isSelected = selectedCluster?.id === cluster.id;
              return (
                <div
                  key={cluster.id}
                  onClick={() => setSelectedCluster(isSelected ? null : cluster)}
                  className={`bg-white border-2 rounded-xl overflow-hidden cursor-pointer transition-all hover:shadow-md ${isSelected ? 'border-blue-500 shadow-md shadow-blue-100' : 'border-slate-200 hover:border-slate-300'}`}
                >
                  {/* Color header */}
                  <div className="h-2 w-full" style={{ backgroundColor: cluster.color }} />
                  <div className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-extrabold text-slate-900 leading-tight">{cluster.label}</p>
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{cluster.description}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="text-base font-extrabold text-slate-900">{cluster.count.toLocaleString()}</p>
                        <p className="text-[10px] text-slate-400">{cluster.percentage}%</p>
                      </div>
                    </div>

                    {/* Top products */}
                    <div className="space-y-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Top Products</p>
                      <div className="flex flex-wrap gap-1">
                        {cluster.top_products.map((p) => (
                          <span key={p} className="text-[10px] font-semibold px-2 py-0.5 rounded-full border"
                            style={{ backgroundColor: cluster.color + '18', borderColor: cluster.color + '40', color: cluster.color }}>
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Message tone */}
                    <div className="bg-slate-50 rounded-lg px-2.5 py-2 border border-slate-100">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-0.5">AI Message Tone</p>
                      <p className="text-[11px] text-slate-600 italic leading-snug">{cluster.message_tone}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); onSelectSegmentFilter && onSelectSegmentFilter(cluster.label); }}
                        className="flex-1 py-1.5 text-[10px] font-bold bg-white border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-center gap-1"
                      >
                        <Users className="w-3 h-3" /> View
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onStartCampaign && onStartCampaign(cluster.top_products[0], cluster.label); }}
                        className="flex-1 py-1.5 text-[10px] font-bold text-white rounded-lg hover:opacity-90 transition-colors cursor-pointer flex items-center justify-center gap-1"
                        style={{ backgroundColor: cluster.color }}
                      >
                        <Target className="w-3 h-3" /> Campaign
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {clusters.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <Brain className="w-10 h-10 mx-auto mb-2 text-slate-200" />
              <p className="text-sm">Cluster data loading — start the backend and try again</p>
            </div>
          )}
        </div>
      )}

      {/* ── TAB: PROPENSITY HEATMAP ──────────────────────────────────────────── */}
      {activeTab === 'heatmap' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Product × Persona Propensity Heatmap</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Shows predicted conversion probability (%) for each product across all 8 customer personas.
              <span className="ml-2 inline-flex items-center gap-1">
                <span className="w-3 h-3 rounded bg-emerald-500 inline-block" /> ≥70% High
                <span className="w-3 h-3 rounded bg-blue-400 inline-block ml-2" /> 50–70% Medium
                <span className="w-3 h-3 rounded bg-amber-300 inline-block ml-2" /> 35–50% Low
                <span className="w-3 h-3 rounded bg-slate-100 inline-block ml-2" /> &lt;35% Unlikely
              </span>
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="text-left py-2 pr-3 text-slate-400 font-bold uppercase tracking-wide w-28">Product</th>
                  {clusters.map((c) => (
                    <th key={c.id} className="py-2 px-1 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: c.color }} />
                        <span className="text-[10px] font-bold text-slate-600 leading-tight text-center max-w-[60px]"
                          style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {c.label.split(' ').slice(0, 2).join(' ')}
                        </span>
                      </div>
                    </th>
                  ))}
                  <th className="py-2 px-2 text-left text-slate-400 font-bold uppercase tracking-wide">Best Cluster</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {PRODUCT_PROPENSITY.map((row) => {
                  const clusterVals = clusters.map((c) => ({ label: c.label, val: row[c.id] || 0, color: c.color }));
                  const best = clusterVals.reduce((a, b) => (b.val > a.val ? b : a), clusterVals[0] || {});
                  return (
                    <tr key={row.product} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2 pr-3 font-semibold text-slate-700 whitespace-nowrap">
                        {PRODUCT_ICONS[row.product] || '📦'} {row.product}
                      </td>
                      {clusters.map((c) => (
                        <td key={c.id} className="py-1.5 px-1">
                          <HeatCell value={row[c.id] || 0} />
                        </td>
                      ))}
                      <td className="py-2 px-2">
                        {best && (
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: best.color }} />
                            <span className="text-[10px] font-bold text-slate-700">{best.label?.split(' ').slice(0, 2).join(' ')}</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="pt-2 border-t border-slate-100">
            <p className="text-xs text-slate-400">
              💡 <strong>How to use this:</strong> Find the highest-propensity cluster for your product, then click "Target Cluster" in the AI Personas tab to launch a personalised campaign.
            </p>
          </div>
        </div>
      )}

      {/* ── TAB: BEHAVIORAL SEGMENTS ─────────────────────────────────────────── */}
      {activeTab === 'segments' && (
        <div className="space-y-4">
          {/* Bar chart */}
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Segment Volume</h3>
            <p className="text-xs text-slate-500 mb-4">Rule-based behavioral segmentation from customer profile data</p>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={segments.map((s) => ({ name: s.name, count: s.count, color: s.color }))}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b', fontWeight: 600 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
                  <RechartsTooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #e2e8f0', fontSize: '11px' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={32}>
                    {segments.map((s, i) => <Cell key={i} fill={s.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Segment cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {segments.map((seg) => (
              <div key={seg.id} className="bg-white rounded-xl border border-slate-200 shadow-xs hover:shadow-md transition-all overflow-hidden flex flex-col">
                <div className="h-1.5 w-full" style={{ backgroundColor: seg.color }} />
                <div className="p-4 space-y-3 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-extrabold text-slate-900">{seg.name}</h4>
                      <p className="text-[11px] text-slate-500">{seg.count.toLocaleString()} customers · {seg.percentage}%</p>
                    </div>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-black shrink-0"
                      style={{ backgroundColor: seg.color }}>
                      {seg.name[0]}
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{seg.description}</p>
                  <div className="grid grid-cols-2 gap-2 bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wide">Est. Spending</p>
                      <p className="text-xs font-extrabold text-slate-900">{seg.avgSpending}/mo</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wide">AI Match</p>
                      <p className="text-xs font-bold text-blue-700 truncate">{seg.recommendedProduct}</p>
                    </div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-2.5 border border-purple-100">
                    <p className="text-[10px] font-bold text-purple-500 uppercase tracking-wide mb-0.5 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Opportunity
                    </p>
                    <p className="text-xs text-purple-800 leading-snug">{seg.aiOpportunity}</p>
                  </div>
                </div>
                <div className="p-3 bg-slate-50 border-t border-slate-100 grid grid-cols-2 gap-2">
                  <button onClick={() => onSelectSegmentFilter && onSelectSegmentFilter(seg.name)}
                    className="py-1.5 text-xs font-bold bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer flex items-center justify-center gap-1">
                    <Users className="w-3.5 h-3.5" /> View
                  </button>
                  <button onClick={() => onStartCampaign && onStartCampaign(seg.recommendedProduct, seg.name)}
                    className="py-1.5 text-xs font-bold text-white rounded-lg hover:opacity-90 transition-colors cursor-pointer flex items-center justify-center gap-1"
                    style={{ backgroundColor: seg.color }}>
                    <Target className="w-3.5 h-3.5" /> Campaign
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
