import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, Sparkles, Plane, CreditCard, TrendingUp, BadgeDollarSign,
  Briefcase, Send, MapPin, Mail, MessageSquare, Phone, CheckCircle2,
  AlertTriangle, Zap, Activity, ArrowUpRight, ArrowDownLeft, RefreshCw,
  Shield, PiggyBank, User, Heart, Car, Home, GraduationCap, Coins,
  BarChart2, Target, Award, ChevronRight, Info, Clock,
} from 'lucide-react';
import OfferSuccessModal from '../components/OfferSuccessModal';
import { analyzeCustomer, createCampaign, generatePersonalisedMessage } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Cell,
} from 'recharts';

const TABS = [
  { id: 'overview',    label: 'Overview',          icon: User },
  { id: 'spending',    label: 'Spending Patterns',  icon: Activity },
  { id: 'cards',       label: 'Cards',              icon: CreditCard },
  { id: 'loans',       label: 'Loans',              icon: BadgeDollarSign },
  { id: 'investments', label: 'Investments',        icon: TrendingUp },
  { id: 'insurance',   label: 'Insurance',          icon: Shield },
  { id: 'nbo',         label: 'NBO Propensity',     icon: Target },
];

const SPEND_CATEGORY_COLORS = {
  Travel: '#3B82F6', Dining: '#F59E0B', Shopping: '#8B5CF6',
  Groceries: '#10B981', Transport: '#06B6D4', Entertainment: '#EC4899',
  Medical: '#EF4444', Education: '#6366F1', Investment: '#059669',
  Insurance: '#D97706', Fuel: '#78716C', Utilities: '#64748B',
  Rent: '#0891B2', EMI: '#DC2626', Other: '#94A3B8',
};

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function fmtCur(val) {
  const n = Number(val) || 0;
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000)   return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000)     return `₹${(n / 1000).toFixed(1)}K`;
  return `₹${n.toFixed(0)}`;
}

function ScoreBar({ score, max = 100, color = '#3B82F6' }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  return (
    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

function CreditScoreGauge({ score }) {
  const pct = Math.min(100, Math.max(0, ((score - 300) / (900 - 300)) * 100));
  const color = score >= 750 ? '#10B981' : score >= 650 ? '#F59E0B' : '#EF4444';
  const label = score >= 750 ? 'Excellent' : score >= 700 ? 'Good' : score >= 650 ? 'Fair' : 'Poor';
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-12 overflow-hidden">
        <div className="absolute inset-0 w-24 h-24 rounded-full border-8 border-slate-100" />
        <div className="absolute inset-0 w-24 h-24 rounded-full border-8"
          style={{ borderColor: color, clipPath: 'polygon(0 0, 100% 0, 100% 50%, 0 50%)', transform: `rotate(${pct * 1.8 - 180}deg)`, transition: 'transform 1s ease' }} />
        <div className="absolute bottom-0 left-0 right-0 text-center">
          <span className="text-lg font-bold" style={{ color }}>{score}</span>
        </div>
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{label}</span>
    </div>
  );
}

export default function Customer360({ customer, onBack, onNavigateCampaigns }) {
  const { employee } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [draftChannel, setDraftChannel] = useState('email');
  const [isDraftingMsg, setIsDraftingMsg] = useState(false);
  const [draftResult, setDraftResult]   = useState(null);
  const [draftError, setDraftError]     = useState('');
  const [isSent, setIsSent] = useState(false);

  const customerId = customer?.customer_id;

  useEffect(() => {
    if (!customerId) return;
    setLoading(true);
    setError('');
    setAnalysis(null);
    analyzeCustomer(customerId)
      .then(setAnalysis)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [customerId]);

  if (!customer) return (
    <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-4">
      <p className="text-slate-500">No customer selected.</p>
      <button onClick={onBack} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold cursor-pointer">Return to Customer List</button>
    </div>
  );

  const displayName     = `${customer.first_name || ''} ${customer.last_name || ''}`.trim();
  const displayInitials = displayName.slice(0, 2).toUpperCase();
  const creditScore     = customer.credit_score || 0;
  const annualIncome    = customer.annual_income || 0;

  // Derived from analysis
  const holdings   = analysis?.holdings_summary || {};
  const rawHoldings= analysis?.holdings || {};
  const windows    = analysis?.windows || {};
  const travel     = analysis?.travel_profile || {};
  const cluster    = analysis?.cluster || {};
  const allScores  = analysis?.all_propensity_scores || [];
  const nbo        = analysis?.nbo || {};
  const w90        = windows['90'] || {};
  const categorySpend = w90.category_spend || {};

  // Sort categories by spend
  const spendEntries = Object.entries(categorySpend).sort((a, b) => b[1] - a[1]);
  const totalSpend90 = w90.total_spend || 0;

  // ── Lifecycle Stage ─────────────────────────────────────────────────────────
  const getLifecycle = () => {
    const tenure = customer.account_tenure_years || customer.tenure_months / 12 || 0;
    const spend30  = (windows['30'] || {}).total_spend || 0;
    const spend90  = totalSpend90;
    const txn90    = w90.transaction_count || 0;
    if (txn90 === 0) return { stage: 'Churned',  color: '#EF4444', desc: 'No transactions in 90+ days', emoji: '💤' };
    if (tenure < 0.5) return { stage: 'New',      color: '#8B5CF6', desc: 'Account opened < 6 months ago', emoji: '🆕' };
    if (spend30 > spend90 / 3 * 1.3) return { stage: 'Growing', color: '#10B981', desc: 'Spend increasing month-over-month', emoji: '📈' };
    if (spend30 < spend90 / 3 * 0.6) return { stage: 'At Risk', color: '#F59E0B', desc: 'Spending declined significantly', emoji: '⚠️' };
    return { stage: 'Stable', color: '#3B82F6', desc: 'Consistent engagement', emoji: '✅' };
  };
  const lifecycle = getLifecycle();

  // ── Risk Flags ───────────────────────────────────────────────────────────────
  const getRiskFlags = () => {
    const flags = [];
    const monthlyEmi   = holdings.total_emi_monthly || 0;
    const monthlyInc   = annualIncome / 12;
    const creditUtil   = customer.credit_utilization_ratio || 0;
    const hasInsurance = rawHoldings.insurance_policies?.length > 0;
    const hasSIP       = rawHoldings.investment_products?.some(p => p.product_type?.toLowerCase().includes('sip') || p.product_type?.toLowerCase().includes('mutual'));
    const totalDebt    = holdings.total_outstanding_debt || 0;

    if (monthlyInc > 0 && monthlyEmi / monthlyInc > 0.5)
      flags.push({ type: 'risk', icon: '🔴', text: `EMI is ${((monthlyEmi/monthlyInc)*100).toFixed(0)}% of income — over-leveraged risk`, severity: 'high' });
    if (creditUtil > 0.8)
      flags.push({ type: 'risk', icon: '🔴', text: `Credit utilisation at ${(creditUtil*100).toFixed(0)}% — near limit`, severity: 'high' });
    if (!hasInsurance && annualIncome > 800000)
      flags.push({ type: 'gap', icon: '🟡', text: 'No insurance detected — significant protection gap', severity: 'medium' });
    if (!hasSIP && annualIncome > 500000)
      flags.push({ type: 'gap', icon: '🟡', text: 'No SIP/Mutual Fund — investment opportunity', severity: 'medium' });
    if (totalSpend90 > 0 && monthlyInc > 0 && totalSpend90 / 3 < monthlyInc * 0.3)
      flags.push({ type: 'opportunity', icon: '🟢', text: `High monthly surplus — strong investment appetite`, severity: 'low' });
    if (travel.is_frequent_flyer && !rawHoldings.credit_cards?.some(c => c.card_type?.toLowerCase().includes('travel')))
      flags.push({ type: 'opportunity', icon: '🟢', text: 'Frequent flyer with no travel credit card — prime acquisition target', severity: 'low' });
    return flags;
  };
  const riskFlags = getRiskFlags();

  // ── Synthetic 12-month spend timeline ────────────────────────────────────────
  const spendTimeline = (() => {
    const base = totalSpend90 / 3 || 20000;
    const now = new Date();
    return Array.from({ length: 12 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - 11 + i, 1);
      const variance = 0.7 + Math.random() * 0.6;
      return {
        month: MONTH_LABELS[d.getMonth()],
        spend: Math.round(base * variance),
        isCurrent: i === 11,
      };
    });
  })();

  const handleDraftMessage = async () => {
    setIsDraftingMsg(true);
    setDraftError('');
    setDraftResult(null);
    try {
      const res = await generatePersonalisedMessage({
        customer_id: customerId,
        product: nbo?.specific_product || 'Travel Credit Card',
        channel: draftChannel,
        age_group: 'auto',
      });
      setDraftResult(res);
    } catch (err) {
      setDraftError(err.message);
    } finally {
      setIsDraftingMsg(false);
    }
  };

  // ── Overview Tab ──────────────────────────────────────────────────────────
  const OverviewTab = () => (
    <div className="space-y-4">
      {/* Profile + Credit Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Profile</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              ['Age', customer.age],
              ['Gender', customer.gender],
              ['City', customer.city],
              ['State', customer.state],
              ['Employment', customer.employment_type],
              ['Marital Status', customer.marital_status],
              ['Email', customer.email],
              ['Mobile', customer.mobile_number],
            ].map(([k, v]) => (
              <div key={k}>
                <span className="text-xs text-slate-400">{k}</span>
                <p className="text-sm font-semibold text-slate-800 truncate">{v || '—'}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <div className="bg-white border border-slate-200 rounded-xl p-5 text-center space-y-1">
            <p className="text-xs text-slate-500 font-medium">Credit Score</p>
            <CreditScoreGauge score={creditScore} />
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1">
            <p className="text-xs text-slate-500">Annual Income</p>
            <p className="text-lg font-bold text-slate-900">{fmtCur(annualIncome)}</p>
            <p className="text-xs text-slate-400">Monthly: {fmtCur(annualIncome / 12)}</p>
          </div>
        </div>
      </div>

      {/* Cluster badge */}
      {cluster.cluster_label && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: cluster.cluster_color || '#3B82F6' }}>
            {(cluster.cluster_label || 'S').slice(0, 1)}
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900">{cluster.cluster_label}</p>
            <p className="text-xs text-slate-500">{cluster.cluster_description || 'AI-assigned customer persona'}</p>
          </div>
          <span className="ml-auto text-xs font-medium px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-100">AI Cluster</span>
        </div>
      )}

      {/* Financial snapshot */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Net Worth', value: fmtCur(holdings.net_worth_indicator), color: 'emerald' },
          { label: 'Total Assets', value: fmtCur(holdings.total_assets_value), color: 'blue' },
          { label: 'Total Debt', value: fmtCur(holdings.total_outstanding_debt), color: 'red' },
          { label: 'Monthly EMI', value: fmtCur(holdings.total_emi_monthly), color: 'amber' },
        ].map(({ label, value, color }) => (
          <div key={label} className={`bg-${color}-50 border border-${color}-100 rounded-xl p-3`}>
            <p className={`text-xs text-${color}-600 font-medium`}>{label}</p>
            <p className={`text-base font-bold text-${color}-900 mt-0.5`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Segments */}
      {analysis?.segments?.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Segments</p>
          <div className="flex flex-wrap gap-2">
            {analysis.segments.map((seg) => (
              <span key={seg} className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">{seg}</span>
            ))}
          </div>
        </div>
      )}

      {/* Travel Profile */}
      {travel.is_frequent_flyer && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Plane className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-bold text-blue-900">✈️ Frequent Flyer Detected</p>
            <p className="text-xs text-blue-700 mt-0.5">
              {fmtCur(travel.flight_spend_90d)} in flights + {fmtCur(travel.hotel_spend_90d)} hotels in last 90 days.
              {travel.international_txn_count > 0 && ` ${travel.international_txn_count} international transactions.`}
            </p>
          </div>
        </div>
      )}

      {/* Lifecycle Stage + Risk Flags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Lifecycle */}
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Lifecycle Stage</p>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg" style={{ backgroundColor: lifecycle.color + '22', border: `2px solid ${lifecycle.color}` }}>
              {lifecycle.emoji}
            </div>
            <div>
              <p className="text-base font-extrabold" style={{ color: lifecycle.color }}>{lifecycle.stage}</p>
              <p className="text-xs text-slate-500">{lifecycle.desc}</p>
            </div>
          </div>
        </div>

        {/* Risk Flags */}
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">AI Risk &amp; Opportunity Flags</p>
          {riskFlags.length === 0 ? (
            <p className="text-xs text-slate-400 flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> No risk flags detected</p>
          ) : (
            <div className="space-y-1.5">
              {riskFlags.map((f, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="shrink-0">{f.icon}</span>
                  <span className={f.severity === 'high' ? 'text-red-700 font-semibold' : f.severity === 'medium' ? 'text-amber-700' : 'text-emerald-700'}>{f.text}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ── Spending Tab ─────────────────────────────────────────────────────────
  const SpendingTab = () => (
    <div className="space-y-4">
      {/* 12-month timeline */}
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">12-Month Spend Timeline</h3>
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={spendTimeline} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 9, fill: '#94a3b8', fontWeight: 600 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
              <RechartsTooltip
                contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '11px' }}
                formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'Spend']}
              />
              <Bar dataKey="spend" radius={[3, 3, 0, 0]} barSize={18}>
                {spendTimeline.map((entry, i) => (
                  <Cell key={i} fill={entry.isCurrent ? '#3B82F6' : '#e2e8f0'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-[10px] text-slate-400 mt-1">* Monthly spend estimates based on 90-day transaction window. Blue = current month.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { label: 'Total Spend (90d)', value: fmtCur(totalSpend90) },
          { label: 'Transactions (90d)', value: w90.transaction_count || 0 },
          { label: 'Digital Ratio', value: `${((w90.digital_ratio || 0) * 100).toFixed(0)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-lg font-bold text-slate-900 mt-0.5">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-slate-500 mb-4 uppercase tracking-wide">Category Breakdown (90 days)</h3>
        <div className="space-y-3">
          {spendEntries.filter(([, v]) => v > 0).slice(0, 10).map(([cat, amt]) => (
            <div key={cat} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700">{cat}</span>
                <span className="text-slate-500">{fmtCur(amt)} ({totalSpend90 > 0 ? ((amt / totalSpend90) * 100).toFixed(1) : 0}%)</span>
              </div>
              <ScoreBar score={(totalSpend90 > 0 ? (amt / totalSpend90) : 0) * 100} color={SPEND_CATEGORY_COLORS[cat] || '#64748B'} />
            </div>
          ))}
          {spendEntries.length === 0 && <p className="text-sm text-slate-400 text-center py-4">No spending data available</p>}
        </div>
      </div>

      {/* Window comparison */}
      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-slate-500 mb-4 uppercase tracking-wide">Spending Windows</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[30, 90, 365].map((days) => {
            const w = windows[String(days)] || {};
            return (
              <div key={days} className="border border-slate-100 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-500">{days}d</p>
                <p className="text-sm font-bold text-slate-900 mt-1">{fmtCur(w.total_spend || 0)}</p>
                <p className="text-xs text-slate-400">{w.transaction_count || 0} txns</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  // ── Cards Tab ─────────────────────────────────────────────────────────────
  const CardsTab = () => {
    const creditCards = rawHoldings.credit_cards || [];
    const debitCards  = rawHoldings.debit_cards  || [];
    return (
      <div className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Total Credit Limit</p>
            <p className="text-lg font-bold text-slate-900">{fmtCur(holdings.total_credit_limit)}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Outstanding Balance</p>
            <p className="text-lg font-bold text-red-600">{fmtCur(holdings.total_credit_outstanding)}</p>
          </div>
        </div>
        {/* Credit Cards */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Credit Cards ({creditCards.length})</h3>
          {creditCards.length > 0 ? (
            <div className="space-y-3">
              {creditCards.map((card, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gradient-to-r from-slate-800 to-slate-700 rounded-xl text-white">
                  <CreditCard className="w-5 h-5 text-slate-300 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold">{card.card_name || card.card_type || 'Credit Card'}</p>
                    <p className="text-xs text-slate-300">Limit: {fmtCur(card.credit_limit)} · Outstanding: {fmtCur(card.outstanding_balance || 0)}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${card.card_status === 'Active' ? 'bg-emerald-500 text-white' : 'bg-slate-500 text-white'}`}>{card.card_status || 'Active'}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-slate-400 text-center py-4">No credit cards</p>}
        </div>
        {/* Debit Cards */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Debit Cards ({debitCards.length})</h3>
          {debitCards.length > 0 ? (
            <div className="space-y-2">
              {debitCards.map((card, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl text-white">
                  <CreditCard className="w-5 h-5 text-blue-200 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold">{card.card_name || card.card_type || 'Debit Card'}</p>
                    <p className="text-xs text-blue-200">{card.account_number || '— '}</p>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-blue-400 text-white">{card.card_status || 'Active'}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-slate-400 text-center py-4">No debit cards</p>}
        </div>
      </div>
    );
  };

  // ── Loans Tab ─────────────────────────────────────────────────────────────
  const LoansTab = () => {
    const loans = rawHoldings.loans || [];
    const activeLoans = loans.filter(l => String(l.loan_status || '').toLowerCase() === 'active');
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Total Outstanding Debt</p>
            <p className="text-lg font-bold text-red-600">{fmtCur(holdings.total_outstanding_debt)}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Monthly EMI Burden</p>
            <p className="text-lg font-bold text-amber-600">{fmtCur(holdings.total_emi_monthly)}</p>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Active Loans ({activeLoans.length})</h3>
          {activeLoans.length > 0 ? (
            <div className="space-y-3">
              {activeLoans.map((loan, i) => (
                <div key={i} className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-slate-900">{loan.loan_category || loan.loan_type || 'Loan'}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Active</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                    <div><p className="text-slate-400">Outstanding</p><p className="font-bold text-slate-800">{fmtCur(loan.outstanding_amount || loan.loan_amount)}</p></div>
                    <div><p className="text-slate-400">EMI</p><p className="font-bold text-slate-800">{fmtCur(loan.emi_amount || 0)}</p></div>
                    <div><p className="text-slate-400">Rate</p><p className="font-bold text-slate-800">{loan.interest_rate || '—'}%</p></div>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-slate-400 text-center py-6">No active loans</p>}
        </div>
      </div>
    );
  };

  // ── Investments Tab ───────────────────────────────────────────────────────
  const InvestmentsTab = () => {
    const investments = rawHoldings.investments || [];
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Total Investment Value</p>
            <p className="text-lg font-bold text-emerald-600">{fmtCur(holdings.total_assets_value)}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Monthly SIP</p>
            <p className="text-lg font-bold text-blue-600">{fmtCur(holdings.total_sip_monthly)}</p>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Investment Portfolio ({investments.length})</h3>
          {investments.length > 0 ? (
            <div className="space-y-3">
              {investments.map((inv, i) => (
                <div key={i} className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-slate-900">{inv.investment_type || inv.fund_name || 'Investment'}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">{inv.investment_status || 'Active'}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                    <div><p className="text-slate-400">Current Value</p><p className="font-bold text-emerald-800">{fmtCur(inv.current_value)}</p></div>
                    <div><p className="text-slate-400">Invested</p><p className="font-bold text-slate-700">{fmtCur(inv.total_invested_amount || inv.invested_amount || 0)}</p></div>
                    <div><p className="text-slate-400">Monthly SIP</p><p className="font-bold text-blue-700">{fmtCur(inv.monthly_sip_amount || inv.sip_amount || 0)}</p></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 space-y-2">
              <TrendingUp className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm text-slate-400">No investments on record</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ── Insurance Tab ─────────────────────────────────────────────────────────
  const InsuranceTab = () => {
    const policies = rawHoldings.insurance || [];
    const activePolicies = policies.filter(p => !['lapsed', 'cancelled', 'expired'].includes(String(p.policy_status || '').toLowerCase()));
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Total Cover</p>
            <p className="text-lg font-bold text-blue-600">{fmtCur(holdings.total_insurance_cover)}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-xs text-slate-500">Active Policies</p>
            <p className="text-lg font-bold text-slate-900">{activePolicies.length}</p>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Policies ({policies.length})</h3>
          {policies.length > 0 ? (
            <div className="space-y-3">
              {policies.map((pol, i) => {
                const isActive = !['lapsed', 'cancelled', 'expired'].includes(String(pol.policy_status || '').toLowerCase());
                const typeIcons = { 'Life': Heart, 'Health': Heart, 'Motor': Car, 'Home': Home, 'Travel': Plane };
                const TypeIcon = typeIcons[pol.insurance_type] || Shield;
                return (
                  <div key={i} className={`p-4 border rounded-xl ${isActive ? 'bg-blue-50 border-blue-100' : 'bg-slate-50 border-slate-200 opacity-60'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <TypeIcon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                      <span className="text-sm font-bold text-slate-900">{pol.insurance_type || 'Insurance'} Insurance</span>
                      <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full ${isActive ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'}`}>{pol.policy_status || 'Unknown'}</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                      <div><p className="text-slate-400">Sum Insured</p><p className="font-bold text-slate-800">{fmtCur(pol.sum_insured || 0)}</p></div>
                      <div><p className="text-slate-400">Premium</p><p className="font-bold text-slate-800">{fmtCur(pol.premium_amount || 0)}/yr</p></div>
                      <div><p className="text-slate-400">Expiry</p><p className="font-bold text-slate-800">{pol.policy_end_date ? new Date(pol.policy_end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</p></div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-6 space-y-2">
              <Shield className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm text-slate-400">No insurance policies on record</p>
              {annualIncome > 600000 && <p className="text-xs text-amber-600 font-medium">⚠️ Insurance gap detected for high-income customer</p>}
            </div>
          )}
        </div>
      </div>
    );
  };

  // ── NBO Propensity Tab ────────────────────────────────────────────────────
  const NboTab = () => {
    // Group all scores by product_type category
    const CATEGORY_CONFIG = [
      { key: 'credit_card',       label: '💳 Credit Cards',   types: ['credit_card', 'credit_card_upgrade'] },
      { key: 'loan',              label: '🏦 Loans',           types: ['loan'] },
      { key: 'investment',        label: '📈 Investments',     types: ['investment'] },
      { key: 'insurance',         label: '🛡️ Insurance',       types: ['insurance'] },
      { key: 'other',             label: '📦 Other Services',  types: [] }, // catch-all
    ];

    const grouped = {};
    CATEGORY_CONFIG.forEach(c => { grouped[c.key] = []; });

    allScores.forEach(item => {
      const t = (item.product_type || '').toLowerCase();
      const cat = CATEGORY_CONFIG.find(c => c.types.includes(t));
      if (cat) {
        grouped[cat.key].push(item);
      } else {
        grouped['other'].push(item);
      }
    });

    // Helper: get the most relevant evidence string for the given product type
    const getRelevantEvidence = (item) => {
      const evidence = item.fit_evidence || [];
      const t = (item.product_type || '').toLowerCase();
      // Filter evidence that is NOT about insurance if this is not an insurance product
      const filtered = t.includes('insurance')
        ? evidence
        : evidence.filter(e => !e.toLowerCase().includes('insurance premium'));
      return filtered[0] || null;
    };

    const ScoreRow = ({ item, i }) => {
      const score = item.nbo_score || 0;
      const pct = Math.round(score * 100);
      const barColor = pct >= 60 ? '#10B981' : pct >= 40 ? '#3B82F6' : pct >= 20 ? '#F59E0B' : '#94A3B8';
      const evidence = getRelevantEvidence(item);
      return (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
              <span className="font-medium text-slate-800">{item.product_name || item.specific_product}</span>
              {item.is_upgrade && <span className="text-[10px] font-bold px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full">UPGRADE</span>}
            </div>
            <span className="font-bold" style={{ color: barColor }}>{pct}%</span>
          </div>
          <ScoreBar score={pct} color={barColor} />
          {evidence && (
            <p className="text-[10px] text-slate-400 pl-6">{evidence}</p>
          )}
        </div>
      );
    };

    return (
      <div className="space-y-4">
        {/* Best Offer */}
        {nbo.specific_product && (
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-yellow-300" />
              <span className="text-xs font-semibold text-blue-100 uppercase tracking-wide">Top NBO Recommendation</span>
            </div>
            <p className="text-xl font-bold">{nbo.specific_product}</p>
            <p className="text-sm text-blue-100 mt-0.5">Propensity: {nbo.propensity}</p>
            {nbo.is_upgrade && <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold bg-white/20 px-2 py-0.5 rounded-full">⬆️ Upgrade Offer</span>}
            {nbo.low_confidence && <p className="text-xs text-yellow-200 mt-2">⚠️ Low confidence — limited transaction history</p>}
          </div>
        )}

        {/* Grouped Propensity Scores */}
        {allScores.length > 0 ? (
          <div className="space-y-4">
            {CATEGORY_CONFIG.map(cat => {
              const items = grouped[cat.key];
              if (!items || items.length === 0) return null;
              return (
                <div key={cat.key} className="bg-white border border-slate-200 rounded-xl p-5">
                  <h3 className="text-xs font-semibold text-slate-500 mb-4 uppercase tracking-wide">
                    {cat.label} — Propensity Ranking
                  </h3>
                  <div className="space-y-3">
                    {items.map((item, i) => (
                      <ScoreRow key={i} item={item} i={i} />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="text-center py-8 space-y-2">
              {loading ? <RefreshCw className="w-6 h-6 text-blue-400 mx-auto animate-spin" /> : <Target className="w-8 h-8 text-slate-300 mx-auto" />}
              <p className="text-sm text-slate-400">{loading ? 'Computing propensity scores…' : 'No propensity data available'}</p>
            </div>
          </div>
        )}

        {/* NBO reasons */}
        {nbo.reasons?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wide">Why This Offer</h3>
            <ul className="space-y-2">
              {nbo.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Draft Message Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Draft Personalised Message</h3>
          <div className="flex gap-2">
            {['email', 'sms'].map((ch) => (
              <button key={ch} onClick={() => setDraftChannel(ch)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg border cursor-pointer transition-colors ${draftChannel === ch ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
                {ch === 'email' ? '✉️ Email' : '💬 SMS'}
              </button>
            ))}
            <button onClick={handleDraftMessage} disabled={isDraftingMsg}
              className="ml-auto px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white border border-blue-600 cursor-pointer hover:bg-blue-700 transition-colors disabled:opacity-60 flex items-center gap-1.5">
              {isDraftingMsg ? <><RefreshCw className="w-3 h-3 animate-spin" /> Generating…</> : <><Sparkles className="w-3 h-3" /> Generate</>}
            </button>
          </div>
          {draftError && <p className="text-xs text-red-500">{draftError}</p>}
          {draftResult && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              {draftResult.subject && <p className="text-xs font-bold text-slate-800 mb-1">📧 {draftResult.subject}</p>}
              <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">{draftResult.body || draftResult.message}</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const TAB_CONTENT = {
    overview: <OverviewTab />,
    spending: <SpendingTab />,
    cards: <CardsTab />,
    loans: <LoansTab />,
    investments: <InvestmentsTab />,
    insurance: <InsuranceTab />,
    nbo: <NboTab />,
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer text-slate-500">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
          {displayInitials}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-bold text-slate-900 truncate">{displayName}</h2>
          <p className="text-xs text-slate-500">{customerId} · {customer.city}</p>
        </div>
        {cluster.cluster_label && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full text-white shrink-0" style={{ backgroundColor: cluster.cluster_color || '#3B82F6' }}>
            {cluster.cluster_label}
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-10 text-blue-600">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span className="text-sm font-medium">Loading 360° profile…</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Tab nav */}
          <div className="flex gap-1 bg-slate-100 rounded-xl p-1 overflow-x-auto scrollbar-hide">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap cursor-pointer transition-all ${activeTab === id ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>{TAB_CONTENT[activeTab]}</div>
        </>
      )}

      <OfferSuccessModal
        isOpen={isOfferModalOpen}
        onClose={() => setIsOfferModalOpen(false)}
        customerName={displayName}
        product={nbo?.specific_product}
        channel={draftChannel}
      />
    </div>
  );
}
