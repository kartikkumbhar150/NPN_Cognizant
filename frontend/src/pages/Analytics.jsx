import React, { useState, useEffect } from 'react';
import {
  TrendingUp, Users, Target, ArrowLeft,
  RefreshCw, AlertTriangle, Megaphone, ChevronRight,
  Clock, CheckCircle2, Sparkles, Send,
  Mail, MessageSquare, Smartphone, Zap,
  Award, Flame, Star, Brain, BarChart2
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import { getCampaigns } from '../services/api';

// ─── Dummy data generator ────────────────────────────────────────────────────

const PRODUCT_BENCHMARKS = {
  'Travel Credit Card':     { openRate: 34, clickRate: 18, convRate: 8.2,  bestAge: 'millennial', bestHour: 18 },
  'Premium Account':        { openRate: 41, clickRate: 22, convRate: 6.5,  bestAge: 'genx',       bestHour: 10 },
  'SIP / Mutual Fund':      { openRate: 29, clickRate: 15, convRate: 5.8,  bestAge: 'millennial', bestHour: 9  },
  'Personal Loan':          { openRate: 52, clickRate: 31, convRate: 14.3, bestAge: 'millennial', bestHour: 13 },
  'Credit Card':            { openRate: 38, clickRate: 24, convRate: 9.1,  bestAge: 'genz',       bestHour: 20 },
  'Home Loan':              { openRate: 26, clickRate: 13, convRate: 4.9,  bestAge: 'genx',       bestHour: 11 },
  'Auto Loan':              { openRate: 33, clickRate: 19, convRate: 7.6,  bestAge: 'millennial', bestHour: 12 },
  'Education Loan':         { openRate: 45, clickRate: 28, convRate: 11.2, bestAge: 'genz',       bestHour: 16 },
  'Life Insurance':         { openRate: 22, clickRate: 11, convRate: 3.8,  bestAge: 'genx',       bestHour: 10 },
  'Health Insurance':       { openRate: 31, clickRate: 17, convRate: 6.2,  bestAge: 'boomer',     bestHour: 9  },
  'Fixed Deposit':          { openRate: 28, clickRate: 14, convRate: 5.1,  bestAge: 'boomer',     bestHour: 10 },
  'NPS':                    { openRate: 25, clickRate: 12, convRate: 4.4,  bestAge: 'genx',       bestHour: 11 },
  'Salary Account':         { openRate: 47, clickRate: 29, convRate: 12.8, bestAge: 'millennial', bestHour: 9  },
  'Gold Loan':              { openRate: 55, clickRate: 36, convRate: 16.7, bestAge: 'boomer',     bestHour: 14 },
};

const CHANNEL_MULTIPLIERS = {
  Email:    { openMult: 1.0, clickMult: 1.0, convMult: 1.0 },
  SMS:      { openMult: 1.4, clickMult: 0.7, convMult: 1.2 },
  WhatsApp: { openMult: 1.6, clickMult: 1.3, convMult: 1.5 },
  Push:     { openMult: 1.3, clickMult: 0.9, convMult: 1.1 },
};

const AGE_LABELS = {
  genz: 'Gen Z (≤25)',
  millennial: 'Millennial (26–40)',
  genx: 'Gen X (41–55)',
  boomer: 'Boomer (55+)',
};

const AGE_COLORS_MAP = {
  genz:      { color: '#ec4899', bg: 'bg-pink-50 text-pink-700 border-pink-200',     icon: Flame     },
  millennial:{ color: '#9333ea', bg: 'bg-purple-50 text-purple-700 border-purple-200', icon: Award  },
  genx:      { color: '#3b82f6', bg: 'bg-blue-50 text-blue-700 border-blue-200',     icon: TrendingUp },
  boomer:    { color: '#10b981', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Star },
};

const CHANNEL_ICONS = { Email: Mail, SMS: MessageSquare, WhatsApp: Smartphone, Push: Zap };

const STATUS_STYLES = {
  active:    'bg-emerald-100 text-emerald-700 border-emerald-200',
  completed: 'bg-blue-100 text-blue-700 border-blue-200',
  draft:     'bg-slate-100 text-slate-600 border-slate-200',
  paused:    'bg-amber-100 text-amber-700 border-amber-200',
};

// Seeded random for consistent dummy data per campaign id
function seededRand(seed, min, max) {
  const x = Math.sin(seed + 1) * 10000;
  const r = x - Math.floor(x);
  return parseFloat((min + r * (max - min)).toFixed(1));
}

function generateDummyAnalytics(campaign) {
  const product = campaign.product || 'Credit Card';
  const channel = campaign.channel || 'Email';
  const audience = campaign.audience_count || 500;
  const seed = (campaign.id || 1) * 37;

  const bench = PRODUCT_BENCHMARKS[product] || PRODUCT_BENCHMARKS['Credit Card'];
  const mult = CHANNEL_MULTIPLIERS[channel] || CHANNEL_MULTIPLIERS.Email;

  const openRate = Math.min(parseFloat((bench.openRate * mult.openMult + seededRand(seed, -3, 3)).toFixed(1)), 95);
  const clickRate = Math.min(parseFloat((bench.clickRate * mult.clickMult + seededRand(seed + 1, -2, 2)).toFixed(1)), openRate);
  const convRate = Math.min(parseFloat((bench.convRate * mult.convMult + seededRand(seed + 2, -1, 1)).toFixed(1)), clickRate);
  const unsubRate = parseFloat(seededRand(seed + 3, 0.3, 1.8).toFixed(1));

  const sent = audience;
  const delivered = Math.round(sent * 0.97);
  const opened = Math.round(delivered * openRate / 100);
  const clicked = Math.round(opened * clickRate / 100);
  const converted = Math.round(clicked * convRate / 100);

  // Hourly data — peaks at bestHour
  const bestHour = bench.bestHour;
  const hourlyData = Array.from({ length: 24 }, (_, h) => {
    const dist = Math.abs(h - bestHour);
    const base = Math.max(0, 1 - dist / 8);
    const opens = Math.round(opened * base * 0.15 + seededRand(seed + h, 0, opened * 0.02));
    const clicks = Math.round(opens * clickRate / 100);
    return { hour: `${h}:00`, opens, clicks };
  });

  // Age breakdown — best age gets highest conv rate
  const ageOrder = ['genz', 'millennial', 'genx', 'boomer'];
  const ageBreakdown = ageOrder.map((key, i) => {
    const isBest = key === bench.bestAge;
    const fraction = isBest ? 0.35 : seededRand(seed + i * 7, 0.1, 0.22);
    const count = Math.round(audience * fraction);
    const ageConvRate = isBest
      ? parseFloat((convRate * 1.4 + seededRand(seed + i, -0.5, 0.5)).toFixed(1))
      : parseFloat((convRate * seededRand(seed + i + 1, 0.4, 0.9)).toFixed(1));
    const ageOpenRate = isBest
      ? parseFloat((openRate * 1.2).toFixed(1))
      : parseFloat((openRate * seededRand(seed + i + 2, 0.6, 1.0)).toFixed(1));
    return { key, count, convRate: Math.min(ageConvRate, 40), openRate: Math.min(ageOpenRate, 95) };
  });

  // Monthly trend (last 6 months simulated)
  const months = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
  const monthlyTrend = months.map((m, i) => ({
    month: m,
    opens: Math.round(opened * (0.6 + i * 0.08) + seededRand(seed + i * 5, -20, 20)),
    conversions: Math.round(converted * (0.5 + i * 0.1) + seededRand(seed + i * 3, -5, 5)),
  }));

  return {
    performance: { openRate, clickRate, conversionRate: convRate, unsubscribeRate: unsubRate, messagesSent: sent, conversions: converted },
    funnel: [
      { name: 'Sent', value: sent, fill: '#3b82f6' },
      { name: 'Delivered', value: delivered, fill: '#6366f1' },
      { name: 'Opened', value: opened, fill: '#8b5cf6' },
      { name: 'Clicked', value: clicked, fill: '#a855f7' },
      { name: 'Converted', value: converted, fill: '#10b981' },
    ],
    ageBreakdown,
    hourlyData,
    monthlyTrend,
    bestHour,
    bestAge: bench.bestAge,
  };
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function RateBar({ label, value, color = '#3b82f6', suffix = '%' }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-bold text-slate-900">{value}{suffix}</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ─── Campaign List ───────────────────────────────────────────────────────────

function CampaignList({ onSelect }) {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const data = await getCampaigns();
      setCampaigns(Array.isArray(data) ? data : (data.campaigns || []));
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
      <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <p className="text-sm text-slate-500 font-medium">Loading campaigns…</p>
    </div>
  );

  if (error) return (
    <div className="p-10 text-center space-y-3">
      <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
      <p className="text-sm font-bold text-red-700">{error}</p>
      <button onClick={load} className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-2 cursor-pointer">
        <RefreshCw className="w-3.5 h-3.5" /> Retry
      </button>
    </div>
  );

  if (campaigns.length === 0) return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center">
      <Megaphone className="w-12 h-12 text-slate-300" />
      <h3 className="text-base font-bold text-slate-500">No campaigns yet</h3>
      <p className="text-xs text-slate-400">Create your first campaign to see analytics here.</p>
    </div>
  );

  return (
    <div className="space-y-3">
      {campaigns.map((c) => {
        const dummy = generateDummyAnalytics(c);
        const ChannelIcon = CHANNEL_ICONS[c.channel] || Mail;
        const statusStyle = STATUS_STYLES[c.status?.toLowerCase()] || STATUS_STYLES.draft;

        return (
          <div
            key={c.id}
            onClick={() => onSelect(c)}
            className="bg-white border border-slate-200 rounded-2xl p-5 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4 min-w-0 flex-1">
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
                  <ChannelIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-slate-900 truncate">{c.name || c.campaign_name || `Campaign #${c.id}`}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${statusStyle}`}>
                      {(c.status || 'draft').toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{c.product} · {c.channel} · {(c.audience_count || 0).toLocaleString()} customers</p>
                  <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Unknown date'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-6 shrink-0">
                <div className="text-center hidden sm:block">
                  <p className="text-[10px] text-slate-400 font-medium">Open Rate</p>
                  <p className="text-sm font-extrabold text-slate-800">{dummy.performance.openRate}%</p>
                </div>
                <div className="text-center hidden sm:block">
                  <p className="text-[10px] text-slate-400 font-medium">Conv. Rate</p>
                  <p className="text-sm font-extrabold text-emerald-600">{dummy.performance.conversionRate}%</p>
                </div>
                <div className="text-center hidden sm:block">
                  <p className="text-[10px] text-slate-400 font-medium">Converted</p>
                  <p className="text-sm font-extrabold text-blue-600">{dummy.performance.conversions.toLocaleString()}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Campaign Detail Analytics ───────────────────────────────────────────────

function CampaignDetailAnalytics({ campaign, onBack }) {
  const dummy = generateDummyAnalytics(campaign);
  const { performance, funnel, ageBreakdown, hourlyData, monthlyTrend } = dummy;
  const ChannelIcon = CHANNEL_ICONS[campaign.channel] || Mail;

  const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981'];

  const ageChartData = ageBreakdown.map((a) => ({
    name: AGE_LABELS[a.key] || a.key,
    'Conv. Rate': a.convRate,
    'Open Rate': a.openRate,
    fill: AGE_COLORS_MAP[a.key]?.color || '#94a3b8',
  }));

  return (
    <div className="space-y-6 pb-10 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors cursor-pointer">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-extrabold text-slate-900 tracking-tight truncate">
            {campaign.name || campaign.campaign_name || `Campaign #${campaign.id}`}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
            <ChannelIcon className="w-3.5 h-3.5" />
            {campaign.product} · {campaign.channel} · {(campaign.audience_count || 0).toLocaleString()} customers
          </p>
        </div>

      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Messages Sent', value: performance.messagesSent.toLocaleString(), icon: Send, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Open Rate', value: `${performance.openRate}%`, icon: Target, color: 'text-purple-600', bg: 'bg-purple-50' },
          { label: 'Click Rate', value: `${performance.clickRate}%`, icon: TrendingUp, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: 'Conversions', value: performance.conversions.toLocaleString(), icon: CheckCircle2, color: 'text-amber-600', bg: 'bg-amber-50' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-2xl p-4 space-y-2">
            <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center`}>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <p className="text-xs text-slate-500 font-medium">{label}</p>
            <p className="text-2xl font-extrabold text-slate-900">{value}</p>
          </div>
        ))}
      </div>

      {/* Rate Bars */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4">
        <h4 className="text-sm font-bold text-slate-800">Engagement Rates</h4>
        <RateBar label="Open Rate" value={performance.openRate} color="#8b5cf6" />
        <RateBar label="Click-Through Rate" value={performance.clickRate} color="#3b82f6" />
        <RateBar label="Conversion Rate" value={performance.conversionRate} color="#10b981" />
        <RateBar label="Unsubscribe Rate" value={performance.unsubscribeRate} color="#ef4444" />
      </div>

      {/* Funnel + Age Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Funnel as Bar Chart */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h4 className="text-sm font-bold text-slate-800 mb-4">Campaign Funnel</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={funnel} layout="vertical" barCategoryGap={8}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={70} />
              <RechartsTooltip formatter={(v) => v.toLocaleString()} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {funnel.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Age Breakdown */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h4 className="text-sm font-bold text-slate-800 mb-4">Age Group Performance</h4>
          <div className="space-y-3">
            {ageBreakdown.map((a) => {
              const cfg = AGE_COLORS_MAP[a.key];
              const Icon = cfg.icon;
              const isBest = a.key === dummy.bestAge;
              return (
                <div key={a.key} className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl border ${cfg.bg} ${isBest ? 'ring-1 ring-offset-1 ring-current' : ''}`}>
                  {isBest && <span className="absolute -top-1.5 -right-1.5 text-[9px] font-bold px-1.5 py-0.5 bg-white border border-current rounded-full">BEST</span>}
                  <span className={`p-1.5 rounded-lg border ${cfg.bg}`}><Icon className="w-3.5 h-3.5" /></span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold">{AGE_LABELS[a.key]}</p>
                    <p className="text-[10px] opacity-70">{a.count.toLocaleString()} customers</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-extrabold">{a.convRate}%</p>
                    <p className="text-[10px] opacity-60">conv. rate</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Hourly Engagement */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <h4 className="text-sm font-bold text-slate-800 mb-1">Hourly Engagement</h4>
        <p className="text-xs text-slate-400 mb-4">Peak engagement at {dummy.bestHour}:00 for this product type</p>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={hourlyData}>
            <defs>
              <linearGradient id="gradOpens" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradClicks" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 9 }} interval={3} />
            <YAxis tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            <Area type="monotone" dataKey="opens" stroke="#8b5cf6" fill="url(#gradOpens)" strokeWidth={2} name="Opens" />
            <Area type="monotone" dataKey="clicks" stroke="#3b82f6" fill="url(#gradClicks)" strokeWidth={2} name="Clicks" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Monthly Trend */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <h4 className="text-sm font-bold text-slate-800 mb-4">Monthly Performance Trend</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={monthlyTrend} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            <Bar dataKey="opens" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Opens" />
            <Bar dataKey="conversions" fill="#10b981" radius={[4, 4, 0, 0]} name="Conversions" />
            <Legend />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* AI Insight Banner */}
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-5 space-y-2">
        <div className="flex items-center gap-2 font-bold text-purple-800 text-sm">
          <Sparkles className="w-4 h-4" /> AI-Generated Insights
        </div>
        <p className="text-xs text-purple-700">• <strong>{AGE_LABELS[dummy.bestAge]}</strong> responded best — {dummy.ageBreakdown.find(a => a.key === dummy.bestAge)?.convRate}% conversion rate vs campaign average {performance.conversionRate}%.</p>
        <p className="text-xs text-purple-700">• Engagement peaks at <strong>{dummy.bestHour}:00</strong> — consider scheduling future campaigns around this hour for maximum impact.</p>
        <p className="text-xs text-purple-700">• <strong>{campaign.channel}</strong> channel shows {performance.openRate > 35 ? 'above-average' : 'moderate'} open rates for <strong>{campaign.product}</strong>. {performance.openRate > 35 ? 'Continue this channel strategy.' : 'Consider testing WhatsApp for higher engagement.'}</p>
      </div>
    </div>
  );
}

// ─── Main Analytics Page ─────────────────────────────────────────────────────

export default function Analytics({ onNavigateCampaigns }) {
  const [selectedCampaign, setSelectedCampaign] = useState(null);

  return (
    <div className="space-y-6 pb-12">
      {selectedCampaign ? (
        <CampaignDetailAnalytics
          campaign={selectedCampaign}
          onBack={() => setSelectedCampaign(null)}
        />
      ) : (
        <>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Campaign Analytics</h2>
              <p className="text-sm text-slate-500 mt-1">Click any campaign to view detailed performance metrics and AI insights.</p>
            </div>
            <button
              onClick={onNavigateCampaigns}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition-colors cursor-pointer shrink-0"
            >
              <Megaphone className="w-3.5 h-3.5" /> New Campaign
            </button>
          </div>
          <CampaignList onSelect={setSelectedCampaign} />
        </>
      )}
    </div>
  );
}
