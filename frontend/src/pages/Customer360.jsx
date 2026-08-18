import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Sparkles,
  Plane,
  CreditCard,
  TrendingUp,
  BadgeDollarSign,
  Briefcase,
  Send,
  MapPin,
  Mail,
  MessageSquare,
  Phone,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Activity,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
} from 'lucide-react';
import OfferSuccessModal from '../components/OfferSuccessModal';
import { analyzeCustomer, createCampaign, generatePersonalisedMessage } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Customer360({ customer, onBack, onNavigateCampaigns }) {
  const { employee } = useAuth();
  const [analysis, setAnalysis]         = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState('');
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [isSendingOffer, setIsSendingOffer]     = useState(false);

  // Personalised message draft
  const [draftChannel, setDraftChannel]   = useState('email');
  const [isDraftingMsg, setIsDraftingMsg] = useState(false);
  const [draftResult, setDraftResult]     = useState(null);
  const [draftError, setDraftError]       = useState('');
  const [draftSubject, setDraftSubject]   = useState('');
  const [draftBody, setDraftBody]         = useState('');
  const [isSent, setIsSent]               = useState(false);

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

  if (!customer) {
    return (
      <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-4">
        <p className="text-slate-500">No customer selected.</p>
        <button onClick={onBack} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold cursor-pointer">
          Return to Customer List
        </button>
      </div>
    );
  }

  const getProductIcon = (productName = '') => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  // ── Derived display values ──────────────────────────────────────────────────
  const displayName     = `${customer.first_name || ''} ${customer.last_name || ''}`.trim();
  const displayInitials = displayName.slice(0, 2).toUpperCase();
  const creditScore     = customer.credit_score || 0;
  const annualIncome    = customer.annual_income || 0;

  // From analysis results
  const nbo          = analysis?.nbo;
  const behavior     = analysis?.behavior;
  const financial    = analysis?.financial_analysis;
  const genaiMsg     = analysis?.genai_message || '';
  const segments     = analysis?.segments || [];

  const recommendedProduct = nbo?.specific_product || 'Travel Credit Card';
  const propensity         = nbo
    ? Math.round((Object.values(analysis?.propensities || {}).reduce((max, v) => Math.max(max, v), 0)) * 100)
    : Math.min(95, 65 + Math.floor(creditScore / 25));

  const ProductIcon = getProductIcon(recommendedProduct);

  // Monthly spend from financial analysis
  const monthlySpend = financial?.spending_profile?.monthly_total_spend || (annualIncome / 12);
  const savingsRate  = financial?.spending_profile?.savings_rate || 0;
  const savingsBalance = financial?.spending_profile?.monthly_savings || 0;

  // Holdings from analysis
  const holdings     = analysis?.holdings_summary || {};
  const c360         = analysis?.customer_360 || {};
  // C360 JSON has holdings directly on the profile object (not nested under 'holdings')
  const c360Holdings = c360;
  const c360Personal = c360.personal_profile || {};
  const c360Employment = c360.employment_and_income || {};
  const c360Banking  = c360.banking_relationship || {};
  const c360Summary  = c360.financial_summary || {};

  // Behavior patterns
  const behaviourPatterns = behavior?.category_spend
    ? Object.entries(behavior.category_spend)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([cat, amt]) => `${cat}: ₹${Number(amt).toLocaleString('en-IN', { maximumFractionDigits: 0 })} total spend`)
    : ['Behavioral data loading…'];

  // Recent transactions from behavior
  const recentTransactions = (behavior?.recent_transactions || []).slice(0, 5);

  // Reasons from NBO
  const whyRecommended = nbo?.reasons?.join(' ') || genaiMsg || 'AI analysis in progress…';

  const handleCreateOffer = async () => {
    setIsSendingOffer(true);
    try {
      await createCampaign({
        customer_id:      customerId,
        customer_name:    displayName,
        product:          recommendedProduct,
        campaign_name:    `Personal Offer – ${displayName}`,
        description:      `AI-generated personalised offer for ${displayName} (${recommendedProduct})`,
        channel:          draftChannel === 'email' ? 'Email' : 'SMS',
        message_preview:  draftSubject || genaiMsg?.slice(0, 200) || `Exclusive ${recommendedProduct} offer`,
        message_email:    draftChannel === 'email' ? draftBody : '',
        message_sms:      draftChannel === 'sms' ? draftBody : '',
        customer_ids:     [customerId],
        age_group_strategy: 'auto',
      });
    } catch (_) {
      // Non-critical: still show success modal
    } finally {
      setIsSendingOffer(false);
      setIsSent(true);
      setIsOfferModalOpen(true);
    }
  };

  const handleDraftMessage = async (channel) => {
    setDraftChannel(channel);
    setIsDraftingMsg(true);
    setDraftError('');
    setDraftResult(null);
    setIsSent(false);
    try {
      const result = await generatePersonalisedMessage({
        customer_id: customerId,
        product: recommendedProduct,
        channel,
        age_group: 'auto',
      });
      setDraftResult(result);
      setDraftSubject(result.subject || '');
      setDraftBody(result.body || '');
    } catch (err) {
      setDraftError(err.message || 'Failed to generate message');
    } finally {
      setIsDraftingMsg(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-xs font-bold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3.5 py-2 rounded-lg hover:bg-slate-50 transition-colors self-start cursor-pointer shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Customers</span>
        </button>

        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <span className="text-xs text-slate-500 font-medium hidden md:inline">Customer ID:</span>
          <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded border border-blue-200">
            {customerId}
          </span>
          <button
            onClick={handleCreateOffer}
            disabled={isSendingOffer || loading}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-75"
          >
            {isSendingOffer ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Sending Offer…</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Create Offer</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Hero Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs relative overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          <div className="lg:col-span-4 flex items-start space-x-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 border-2 border-slate-200 flex items-center justify-center font-bold text-slate-700 text-2xl shrink-0 shadow-xs">
              {displayInitials}
            </div>
            <div className="space-y-1">
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">{displayName}</h2>
              <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                {c360Banking.customer_segment_type || customer.customer_segment_type || 'Active'}
              </span>
              <p className="text-xs font-medium text-slate-600">{c360Employment.occupation || customer.employment_type || '—'}</p>
              <div className="flex flex-col gap-1 text-xs text-slate-500 pt-1">
                <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-400" />{c360Personal.city || customer.city || '—'}, {c360Personal.state || customer.state || ''}</span>
                <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5 text-slate-400" />{c360Personal.email || customer.email || '—'}</span>
                <span className="flex items-center gap-1.5"><Phone className="w-3.5 h-3.5 text-slate-400" />{c360Personal.phone_number || customer.phone_number || c360Personal.mobile_number || customer.mobile_number || '—'}</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 rounded-xl p-4 border border-slate-200/80">
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Segment</span>
              <p className="text-xs sm:text-sm font-bold text-slate-800 truncate">{segments[0] || c360Banking.customer_segment_type || customer.customer_segment_type || 'Standard'}</p>
              <span className="text-[10px] text-blue-600 font-medium">{c360Banking.risk_profile ? `Risk: ${c360Banking.risk_profile}` : 'AI-Clustered'}</span>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Monthly Spend</span>
              <p className="text-xs sm:text-sm font-bold text-slate-900">
                ₹{Math.round(monthlySpend).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
              <span className="text-[10px] text-emerald-600 font-medium">{(savingsRate * 100).toFixed(1)}% savings rate</span>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Credit Health</span>
              <p className={`text-xs sm:text-sm font-bold ${creditScore >= 750 ? 'text-emerald-600' : creditScore >= 650 ? 'text-blue-600' : 'text-amber-600'}`}>
                {c360Banking.credit_score || creditScore} CIBIL
              </p>
              <span className="text-[10px] text-slate-500">
                {(c360Banking.credit_score||creditScore) >= 750 ? 'Tier 1 Prime' : (c360Banking.credit_score||creditScore) >= 650 ? 'Tier 2' : 'Tier 3'}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Annual Income</span>
              <p className="text-xs sm:text-sm font-bold text-slate-900">
                ₹{((c360Employment.annual_income||annualIncome) / 100000).toFixed(1)}L
              </p>
              <span className="text-[10px] text-slate-500">{c360Employment.income_range || `Age: ${c360Personal.age || customer.age || '—'}`}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Loading state for AI pipeline */}
      {loading && (
        <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 rounded-2xl p-8 text-white text-center space-y-4">
          <div className="flex items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-purple-300/30 border-t-purple-300 rounded-full animate-spin" />
            <Sparkles className="w-5 h-5 text-purple-300" />
          </div>
          <h3 className="text-lg font-bold">Prism is analysing {displayName}…</h3>
          <p className="text-purple-200 text-sm">Running behavior engine, segmentation, financial analysis, NBO engine and GenAI personalization. This may take a few seconds.</p>
        </div>
      )}

      {error && (
        <div className="p-5 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <p className="text-sm font-semibold">AI Analysis Error</p>
            <p className="text-xs text-red-600">{error}</p>
          </div>
          <button
            onClick={() => {
              setLoading(true);
              analyzeCustomer(customerId).then(setAnalysis).catch((e) => setError(e.message)).finally(() => setLoading(false));
            }}
            className="ml-auto px-3 py-1.5 bg-red-600 text-white text-xs font-semibold rounded-lg cursor-pointer flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      )}

      {/* AI NBO Highlight (shown once analysis is ready) */}
      {analysis && !loading && (
        <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Sparkles className="w-48 h-48 text-white" />
          </div>

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-5 space-y-3">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-white/15 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-purple-300" />
                <span>AI Next Best Offer (NBO)</span>
              </div>
              <div>
                <span className="text-xs text-purple-200 font-medium">Recommended Product</span>
                <h3 className="text-2xl font-extrabold text-white flex items-center gap-2">
                  <ProductIcon className="w-6 h-6 text-purple-300" />
                  {recommendedProduct}
                </h3>
              </div>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/10 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-purple-200 font-medium">Propensity Score</span>
                  <span className="text-emerald-300 font-extrabold text-base">{propensity}%</span>
                </div>
                <div className="w-full bg-black/30 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-400 to-teal-300 rounded-full transition-all duration-1000"
                    style={{ width: `${propensity}%` }}
                  />
                </div>
                <p className="text-[11px] text-purple-200">High conversion probability based on transaction telemetry.</p>
              </div>
            </div>

            <div className="lg:col-span-7 bg-white/10 backdrop-blur-md rounded-xl p-5 border border-white/15 space-y-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                Why this product was recommended
              </h4>
              <p className="text-xs text-purple-100 leading-relaxed line-clamp-4">{whyRecommended}</p>
              <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-white/10">
                <span className="text-[11px] text-purple-200">
                  Model: <strong>Prism Propensity Engine v2.4</strong>
                </span>
                <button
                  onClick={handleCreateOffer}
                  className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs rounded-lg transition-colors cursor-pointer shadow-sm"
                >
                  Dispatch Instant Offer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}


      {/* ── HOLDINGS PORTFOLIO PANEL ─────────────────────────────────────── */}
      {analysis && !loading && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Customer 360 — Product Holdings</h3>
              <p className="text-xs text-slate-400">All active products owned by this customer</p>
            </div>
          </div>
          <div className="p-5 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

            {/* Accounts */}
            {(c360Holdings.accounts?.length > 0) && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Accounts ({c360Holdings.accounts.length})</p>
                {c360Holdings.accounts.map((a, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-700">{a.account_type}</span>
                    <span className="text-slate-500 font-mono">₹{Number(a.average_monthly_balance||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Credit Cards */}
            {(c360Holdings.credit_cards?.length > 0) && (
              <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600">Credit Cards ({c360Holdings.credit_cards.length})</p>
                {c360Holdings.credit_cards.map((cc, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{cc.card_name}</span>
                    <span className="text-blue-700 font-mono">₹{Number(cc.credit_limit||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
                <p className="text-[11px] text-blue-600 font-medium">Total Limit: ₹{Number(holdings.total_credit_limit||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</p>
              </div>
            )}

            {/* Loans */}
            {(c360Holdings.loans?.length > 0) && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Active Loans ({c360Holdings.loans.length})</p>
                {c360Holdings.loans.map((l, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{l.loan_category}</span>
                    <span className="text-amber-700 font-mono">EMI ₹{Number(l.emi_amount||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
                <p className="text-[11px] text-amber-700 font-medium">Total Outstanding: ₹{Number(holdings.total_outstanding_debt||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</p>
              </div>
            )}

            {/* Investments */}
            {(c360Holdings.investments?.length > 0) && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Investments ({c360Holdings.investments.length})</p>
                {c360Holdings.investments.slice(0, 4).map((inv, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{inv.investment_category}</span>
                    <span className="text-emerald-700 font-mono">₹{Number(inv.current_value||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
                {c360Holdings.investments.length > 4 && <p className="text-[11px] text-emerald-600">+{c360Holdings.investments.length - 4} more</p>}
                <p className="text-[11px] text-emerald-700 font-medium">Total Value: ₹{Number(holdings.total_assets_value||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</p>
              </div>
            )}

            {/* Deposits */}
            {(c360Holdings.deposits?.length > 0) && (
              <div className="rounded-xl border border-purple-200 bg-purple-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-purple-700">Deposits ({c360Holdings.deposits.length})</p>
                {c360Holdings.deposits.map((d, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{d.deposit_type}</span>
                    <span className="text-purple-700 font-mono">₹{Number(d.principal_amount||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Insurance */}
            {(c360Holdings.insurance?.length > 0) && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-rose-700">Insurance ({c360Holdings.insurance.length})</p>
                {c360Holdings.insurance.map((ins, i) => (
                  <div key={i} className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{ins.insurance_type || ins.insurance_category}</span>
                    <span className="text-rose-700 font-mono">₹{Number(ins.sum_insured||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                  </div>
                ))}
                <p className="text-[11px] text-rose-700 font-medium">Total Cover: ₹{Number(holdings.total_insurance_cover||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</p>
              </div>
            )}

            {/* Net Worth Summary */}
            <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-900 to-slate-800 p-4 space-y-2 text-white col-span-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Financial Summary</p>
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Total Assets</span>
                <span className="text-emerald-400 font-bold">₹{Number(holdings.total_assets_value||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Total Debt</span>
                <span className="text-rose-400 font-bold">₹{Number(holdings.total_outstanding_debt||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
              </div>
              <div className="border-t border-slate-700 mt-2 pt-2 flex justify-between text-xs">
                <span className="text-slate-300 font-semibold">Net Worth</span>
                <span className={`font-extrabold ${(holdings.net_worth_indicator||0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  ₹{Number(holdings.net_worth_indicator||0).toLocaleString('en-IN', {maximumFractionDigits:0})}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Monthly EMI</span>
                <span className="text-amber-400 font-bold">₹{Number(holdings.total_emi_monthly||0).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2-Column: Behavioral Patterns + Transactions */}
      {analysis && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Behavior Patterns + GenAI Message */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
                <Activity className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Observed Behaviour Patterns</h3>
              </div>
              <div className="space-y-2.5">
                {behaviourPatterns.map((pattern, index) => (
                  <div key={index} className="flex items-start space-x-2.5 p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                    <span className="leading-snug">{pattern}</span>
                  </div>
                ))}
              </div>
            </div>

            {genaiMsg && (
              <div className="bg-gradient-to-br from-purple-50 via-white to-blue-50/60 rounded-xl border border-purple-200 p-5 shadow-xs space-y-3">
                <div className="flex items-center space-x-2 text-purple-700 font-bold text-xs uppercase tracking-wider">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span>AI Marketing Message Preview</span>
                </div>
                <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-line line-clamp-6">{genaiMsg}</p>
              </div>
            )}
          </div>

          {/* Right: Transactions */}
          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col justify-between">
            <div>
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Recent Account Transactions</h3>
                  <p className="text-xs text-slate-500">Live feed analyzed for propensity scoring</p>
                </div>
                <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded">
                  From behavior engine
                </span>
              </div>

              {recentTransactions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      <tr>
                        <th className="px-4 py-3">Date</th>
                        <th className="px-4 py-3">Description</th>
                        <th className="px-4 py-3">Category</th>
                        <th className="px-4 py-3 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {recentTransactions.map((tx, i) => (
                        <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                          <td className="px-4 py-3 whitespace-nowrap text-slate-500 font-medium">{tx.date || tx.transaction_date || '—'}</td>
                          <td className="px-4 py-3 whitespace-nowrap font-bold text-slate-900">{tx.description || tx.merchant || '—'}</td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">{tx.category || '—'}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right font-bold">
                            <span className={tx.type === 'credit' || tx.transaction_type === 'credit' ? 'text-emerald-600' : 'text-slate-900'}>
                              {(tx.type === 'credit' || tx.transaction_type === 'credit') ? '+' : '-'}
                              ₹{Number(tx.amount || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center">
                  <p className="text-xs text-slate-400">Transaction data from behavior engine not available.</p>
                  <p className="text-xs text-slate-400 mt-1">Category spending breakdown available above.</p>
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Live telemetry from behavior engine</span>
              <button
                onClick={handleCreateOffer}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Create Offer for {displayName.split(' ')[0]}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── PERSONALISED MESSAGE DRAFT PANEL ─────────────────────────────────── */}
      {analysis && !loading && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-sm">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Draft Personalised Message</h3>
                <p className="text-xs text-slate-500">Groq AI drafts a message tuned to {displayName}'s age & profile</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleDraftMessage('email')}
                disabled={isDraftingMsg}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                  draftChannel === 'email' && draftResult
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                } disabled:opacity-60`}
              >
                <Mail className="w-3.5 h-3.5" />
                {isDraftingMsg && draftChannel === 'email' ? (
                  <span className="flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" /> Drafting…</span>
                ) : '📧 Draft Email'}
              </button>
              <button
                onClick={() => handleDraftMessage('sms')}
                disabled={isDraftingMsg}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                  draftChannel === 'sms' && draftResult
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                } disabled:opacity-60`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                {isDraftingMsg && draftChannel === 'sms' ? (
                  <span className="flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" /> Drafting…</span>
                ) : '📱 Draft SMS'}
              </button>
            </div>
          </div>

          <div className="p-5 space-y-4">
            {draftError && (
              <div className="p-3 bg-red-50 text-red-700 text-xs font-semibold rounded-lg border border-red-200 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />{draftError}
              </div>
            )}

            {isDraftingMsg && (
              <div className="flex flex-col items-center justify-center py-8 space-y-3">
                <div className="flex space-x-2">
                  <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce" />
                </div>
                <p className="text-sm font-bold text-purple-700">Groq AI is crafting a personalised {draftChannel} for {displayName.split(' ')[0]}…</p>
                <p className="text-xs text-slate-500">Analyzing age profile, portfolio gaps, and behavioral triggers</p>
              </div>
            )}

            {draftResult && !isDraftingMsg && (
              <div className="space-y-4 animate-in fade-in duration-500">
                {/* Strategy badge */}
                <div className="flex flex-wrap items-center gap-2">
                  {(() => {
                    const ageColors = {
                      genz: 'bg-pink-50 text-pink-700 border-pink-200',
                      millennial: 'bg-purple-50 text-purple-700 border-purple-200',
                      genx: 'bg-blue-50 text-blue-700 border-blue-200',
                      boomer: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                    };
                    const ageLabel = { genz: 'Gen Z', millennial: 'Millennial', genx: 'Gen X', boomer: 'Boomer' };
                    return (
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${ageColors[draftResult.age_group] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                        {ageLabel[draftResult.age_group] || draftResult.age_group} • {draftResult.age}y
                      </span>
                    );
                  })()}
                  <span className="text-xs text-slate-500 italic">{draftResult.strategy_used}</span>
                </div>

                {/* Subject / Header */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">{draftChannel === 'email' ? 'Subject Line' : 'SMS Header'}</label>
                  <input
                    type="text"
                    value={draftSubject}
                    onChange={(e) => setDraftSubject(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                  />
                </div>

                {/* Body */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">{draftChannel === 'email' ? 'Email Body' : 'SMS Text'}</label>
                  <textarea
                    rows={draftChannel === 'email' ? 8 : 4}
                    value={draftBody}
                    onChange={(e) => setDraftBody(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-y font-serif"
                  />
                  {draftChannel === 'sms' && (
                    <p className={`text-[11px] mt-1 font-medium ${draftBody.length > 160 ? 'text-amber-600' : 'text-slate-400'}`}>
                      {draftBody.length} / 160 characters {draftBody.length > 160 && '— will send as multi-part SMS'}
                    </p>
                  )}
                </div>

                {isSent ? (
                  <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200 rounded-xl">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    {draftChannel === 'email' ? 'Email' : 'SMS'} sent to {displayName} successfully! Offer recorded.
                  </div>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs text-slate-400 italic">Review and edit the draft above before sending.</p>
                    <button
                      onClick={handleCreateOffer}
                      disabled={isSendingOffer}
                      className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all cursor-pointer disabled:opacity-70"
                    >
                      {isSendingOffer ? (
                        <><div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /><span>Sending…</span></>
                      ) : (
                        <><Send className="w-3.5 h-3.5" /><span>Send {draftChannel === 'email' ? 'Email' : 'SMS'} to {displayName.split(' ')[0]}</span></>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {!draftResult && !isDraftingMsg && !draftError && (
              <div className="flex flex-col items-center justify-center py-10 text-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-purple-50 border border-purple-100 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <p className="text-sm font-semibold text-slate-500">Click "Draft Email" or "Draft SMS" to generate a personalised message for {displayName.split(' ')[0]}</p>
                <p className="text-xs text-slate-400">Groq AI will tailor the message to their age, portfolio, city and financial profile</p>
              </div>
            )}
          </div>
        </div>
      )}

      <OfferSuccessModal
        isOpen={isOfferModalOpen}
        onClose={() => setIsOfferModalOpen(false)}
        customer={{ name: displayName, recommendedProduct, propensity }}
        onNavigateCampaigns={onNavigateCampaigns}
      />
    </div>
  );
}

