import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, BarChart2, TrendingUp, Users, Target, Sparkles,
  RefreshCw, AlertTriangle, CheckCircle2, Brain, Send,
  Mail, MessageSquare, Clock, Zap, Award, Flame, Star
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, FunnelChart, Funnel, LabelList,
  BarChart, Bar, Cell
} from 'recharts';
import { getCampaignAnalytics, getCampaignInsights } from '../services/api';

const AGE_COLORS = {
  genz: { label: 'Gen Z', color: 'bg-pink-50 text-pink-700 border-pink-200', icon: Flame },
  millennial: { label: 'Millennial', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Award },
  genx: { label: 'Gen X', color: 'bg-blue-50 text-blue-700 border-blue-200', icon: TrendingUp },
  boomer: { label: 'Boomer', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Star },
  auto: { label: 'Auto', color: 'bg-slate-100 text-slate-700 border-slate-200', icon: Brain },
};

function RateBar({ label, value, max = 100, color = '#3b82f6' }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-bold text-slate-900">{value}%</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function CampaignAnalytics({ campaignId, campaignName, onBack }) {
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [insights, setInsights] = useState(null);
  const [loadingInsights, setLoadingInsights] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getCampaignAnalytics(campaignId);
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    setLoadingInsights(true);
    try {
      const res = await getCampaignInsights();
      setInsights(res);
    } catch (_) {}
    finally { setLoadingInsights(false); }
  };

  useEffect(() => { loadData(); }, [campaignId]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <p className="text-sm text-slate-500 font-medium">Loading campaign analytics…</p>
    </div>
  );

  if (error) return (
    <div className="p-10 text-center space-y-3">
      <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
      <p className="text-sm font-bold text-red-700">{error}</p>
      <button onClick={loadData} className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition-colors cursor-pointer inline-flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5" /> Retry
      </button>
    </div>
  );

  const { metrics, rates, channel_breakdown, hourly_opens, performance_flags } = data;
  const sent      = metrics?.sent || 0;
  const opened    = metrics?.opened || 0;
  const clicked   = metrics?.clicked || 0;
  const applied   = metrics?.applied || 0;
  const converted = metrics?.converted || 0;

  const funnelData = [
    { name: 'Sent',      value: sent,      fill: '#3b82f6' },
    { name: 'Opened',    value: opened,    fill: '#6366f1' },
    { name: 'Clicked',   value: clicked,   fill: '#8b5cf6' },
    { name: 'Applied',   value: applied,   fill: '#f59e0b' },
    { name: 'Converted', value: converted, fill: '#10b981' },
  ];

  const channelData = [
    { channel: 'Email', sent: channel_breakdown?.email?.sent || 0, opened: channel_breakdown?.email?.opened || 0 },
    { channel: 'SMS',   sent: channel_breakdown?.sms?.sent || 0,   opened: channel_breakdown?.sms?.opened || 0 },
  ];

  const isLowPerf = performance_flags?.length > 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-xs font-bold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3.5 py-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" /><span>Back to Campaigns</span>
        </button>
        <button onClick={loadData} className="inline-flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer shadow-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 rounded-2xl p-6 text-white border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/4 bg-gradient-to-l from-blue-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-300 text-xs font-semibold">
            <BarChart2 className="w-3.5 h-3.5" /> Campaign Analytics
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight">{data.campaign_name}</h2>
          <p className="text-slate-300 text-xs">
            Product: <strong className="text-white">{data.product}</strong> ·
            Channel: <strong className="text-white">{data.channel}</strong> ·
            Audience: <strong className="text-white">{data.audience_count?.toLocaleString()}</strong>
          </p>
          {isLowPerf && (
            <div className="inline-flex items-center gap-2 mt-2 px-3 py-1.5 bg-amber-500/20 border border-amber-400/30 rounded-xl text-amber-300 text-xs font-semibold">
              <AlertTriangle className="w-3.5 h-3.5" />
              Low performance detected — AI analysis available below
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { label: 'Sent',      value: sent.toLocaleString(),      sub: '100% Dispatched',          color: 'blue',    icon: Send },
          { label: 'Opened',    value: opened.toLocaleString(),    sub: `${rates?.open_rate}% Open Rate`,    color: 'indigo',  icon: Mail },
          { label: 'Clicked',   value: clicked.toLocaleString(),   sub: `${rates?.click_rate}% Click Rate`,  color: 'purple',  icon: Target },
          { label: 'Applied',   value: applied.toLocaleString(),   sub: `${rates?.apply_rate}% Apply Rate`,  color: 'amber',   icon: Zap },
          { label: 'Converted', value: converted.toLocaleString(), sub: `${rates?.overall_conv}% Overall`,   color: 'emerald', icon: CheckCircle2 },
        ].map(({ label, value, sub, color, icon: Icon }) => {
          const colorMap = {
            blue:    'bg-blue-50 text-blue-600',
            indigo:  'bg-indigo-50 text-indigo-600',
            purple:  'bg-purple-50 text-purple-600',
            amber:   'bg-amber-50 text-amber-600',
            emerald: 'bg-emerald-50 text-emerald-600',
          };
          const textMap = {
            blue: 'text-blue-700', indigo: 'text-indigo-700', purple: 'text-purple-700',
            amber: 'text-amber-700', emerald: 'text-emerald-700',
          };
          return (
            <div key={label} className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{label}</span>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <h4 className={`text-xl font-extrabold ${textMap[color]}`}>{value}</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>
            </div>
          );
        })}
      </div>

      {/* 2-col: Conversion Funnel + Rate Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funnel */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900">Conversion Funnel</h3>
            <p className="text-xs text-slate-500">Customer journey from dispatch to conversion</p>
          </div>
          <div className="space-y-3">
            {funnelData.map((stage, i) => {
              const pct = sent > 0 ? ((stage.value / sent) * 100).toFixed(1) : 0;
              return (
                <div key={stage.name} className="relative group">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-bold text-slate-700">{stage.name}</span>
                    <span className="font-semibold text-slate-900">
                      {stage.value.toLocaleString()} <span className="text-slate-400">({pct}%)</span>
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden border border-slate-200/60">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{ width: `${pct}%`, backgroundColor: stage.fill, opacity: 1 - i * 0.08 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Rate Bars */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900">Performance Rates</h3>
            <p className="text-xs text-slate-500">Stage-wise conversion benchmarks</p>
          </div>
          <div className="space-y-4 py-2">
            <RateBar label="Open Rate"           value={rates?.open_rate || 0}    color="#6366f1" />
            <RateBar label="Click-Through Rate"  value={rates?.click_rate || 0}   color="#8b5cf6" />
            <RateBar label="Application Rate"    value={rates?.apply_rate || 0}   color="#f59e0b" />
            <RateBar label="Conversion Rate"     value={rates?.conv_rate || 0}    color="#10b981" />
            <RateBar label="Overall Conversion"  value={rates?.overall_conv || 0} color="#3b82f6" />
          </div>

          {/* Industry benchmark */}
          <div className="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
            <p className="font-bold text-slate-600">Industry Benchmarks (Banking)</p>
            <div className="flex justify-between text-slate-500">
              <span>Email Open Rate</span><span className="font-semibold text-slate-700">25–35%</span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>SMS Open Rate</span><span className="font-semibold text-slate-700">60–80%</span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Conversion Rate</span><span className="font-semibold text-slate-700">2–4%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hourly Opens Chart + Channel Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Hourly Opens */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900">Hourly Open Distribution</h3>
            <p className="text-xs text-slate-500">When customers opened the message (24h view)</p>
          </div>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourly_opens || []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorOpens" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="hour" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} interval={3} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '11px' }} />
                <Area type="monotone" dataKey="opens" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorOpens)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 mt-2">Peak opens typically at 8–10 PM. Schedule next campaign accordingly.</p>
        </div>

        {/* Channel Breakdown */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-4 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900">Channel Breakdown</h3>
            <p className="text-xs text-slate-500">Email vs SMS performance</p>
          </div>
          <div className="space-y-4">
            {channelData.map((ch) => {
              const openPct = ch.sent > 0 ? ((ch.opened / ch.sent) * 100).toFixed(1) : 0;
              const isEmail = ch.channel === 'Email';
              return (
                <div key={ch.channel} className={`p-3.5 rounded-xl border ${isEmail ? 'border-blue-200 bg-blue-50/50' : 'border-emerald-200 bg-emerald-50/50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {isEmail ? <Mail className="w-4 h-4 text-blue-600" /> : <MessageSquare className="w-4 h-4 text-emerald-600" />}
                    <span className={`text-xs font-bold ${isEmail ? 'text-blue-700' : 'text-emerald-700'}`}>{ch.channel}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-slate-500">Sent</p>
                      <p className="font-extrabold text-slate-900">{ch.sent.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Opened</p>
                      <p className={`font-extrabold ${isEmail ? 'text-blue-600' : 'text-emerald-600'}`}>{ch.opened.toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-white rounded-full h-2 overflow-hidden border border-slate-200">
                      <div
                        className={`h-full rounded-full ${isEmail ? 'bg-blue-500' : 'bg-emerald-500'}`}
                        style={{ width: `${openPct}%` }}
                      />
                    </div>
                    <p className={`text-[10px] mt-0.5 font-semibold ${isEmail ? 'text-blue-600' : 'text-emerald-600'}`}>{openPct}% open rate</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Performance Flags */}
      {isLowPerf && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-sm font-bold text-amber-800">Low Performance Detected</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {performance_flags.map((flag) => {
              const flagInfo = {
                LOW_OPEN_RATE: { label: 'Low Open Rate (<30%)', fix: 'Try personalised subject lines with customer name and achievement framing ("Congratulations {Name}!")' },
                LOW_CLICK_RATE: { label: 'Low Click Rate (<20%)', fix: 'Improve CTA button placement. Gen Z responds better to emoji-heavy CTAs, Gen X to specific value propositions.' },
                LOW_CONVERSION: { label: 'Low Overall Conversion (<2%)', fix: 'Mismatched product for segment. Verify NBO engine recommendations or try a different channel (SMS for Gen Z).' },
              };
              const info = flagInfo[flag] || { label: flag, fix: 'Review campaign parameters.' };
              return (
                <div key={flag} className="p-3 bg-white rounded-lg border border-amber-200 text-xs flex-1 min-w-64">
                  <p className="font-bold text-amber-800 mb-1">⚠️ {info.label}</p>
                  <p className="text-amber-700 leading-relaxed">{info.fix}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Insights Panel */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 rounded-2xl p-6 text-white border border-slate-800">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-300" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">AI Self-Learning Insights</h3>
              <p className="text-xs text-purple-200">Groq analyzes performance & recommends improvements for next campaign</p>
            </div>
          </div>
          <button
            onClick={loadInsights}
            disabled={loadingInsights}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600/80 hover:bg-purple-600 text-white text-xs font-bold rounded-xl border border-purple-500/50 transition-colors cursor-pointer disabled:opacity-70"
          >
            {loadingInsights ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{insights ? 'Refresh' : 'Analyze & Improve'}</span>
          </button>
        </div>

        {loadingInsights && (
          <div className="flex items-center gap-3 py-6 justify-center">
            <RefreshCw className="w-5 h-5 text-purple-300 animate-spin" />
            <p className="text-purple-200 text-sm">Groq is analyzing campaign performance patterns…</p>
          </div>
        )}

        {insights && !loadingInsights && (
          <div className="space-y-4 animate-in fade-in duration-500">
            <div className="p-3 bg-white/10 rounded-xl border border-white/10 text-sm text-purple-100">{insights.overall_health}</div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(insights.insights || []).map((insight, i) => {
                const typeStyle = { warning: 'border-amber-400/30 bg-amber-500/10', success: 'border-emerald-400/30 bg-emerald-500/10', info: 'border-blue-400/30 bg-blue-500/10' };
                const typeIcon  = { warning: '⚠️', success: '✅', info: '💡' };
                return (
                  <div key={i} className={`p-4 rounded-xl border ${typeStyle[insight.type] || 'border-white/10 bg-white/5'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span>{typeIcon[insight.type] || '💡'}</span>
                      <h4 className="text-xs font-bold text-white">{insight.title}</h4>
                    </div>
                    <p className="text-xs text-purple-200 leading-relaxed">{insight.description}</p>
                  </div>
                );
              })}
            </div>

            {insights.top_recommendation && (
              <div className="p-4 bg-gradient-to-r from-blue-600/40 to-purple-600/40 rounded-xl border border-blue-400/30">
                <p className="text-xs font-bold text-blue-200 mb-1">🎯 Top Recommendation for Next Campaign</p>
                <p className="text-sm text-white font-semibold">{insights.top_recommendation}</p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              {insights.best_channel && (
                <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                  <p className="font-bold text-purple-200 mb-1">📡 Best Channel</p>
                  <p className="text-white">{insights.best_channel}</p>
                </div>
              )}
              {insights.best_timing && (
                <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                  <p className="font-bold text-purple-200 mb-1">⏰ Best Timing</p>
                  <p className="text-white">{insights.best_timing}</p>
                </div>
              )}
              {insights.next_campaign_suggestion && (
                <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                  <p className="font-bold text-purple-200 mb-1">🚀 Next Campaign</p>
                  <p className="text-white">{insights.next_campaign_suggestion}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {!insights && !loadingInsights && (
          <div className="text-center py-8 text-purple-300 text-sm">
            <Brain className="w-10 h-10 mx-auto mb-3 opacity-40" />
            <p>Click "Analyze & Improve" to get AI-powered recommendations for this campaign.</p>
          </div>
        )}
      </div>
    </div>
  );
}
