import React, { useState } from 'react';
import {
  ArrowLeft,
  Sparkles,
  Plane,
  CreditCard,
  TrendingUp,
  BadgeDollarSign,
  Briefcase,
  ShieldCheck,
  Send,
  Calendar,
  MapPin,
  Mail,
  Phone,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Activity,
  Award,
  Wallet,
  DollarSign,
  ArrowUpRight,
  ArrowDownLeft,
  Sliders,
  ChevronRight
} from 'lucide-react';
import OfferSuccessModal from '../components/OfferSuccessModal';

export default function Customer360({ customer, onBack, onNavigateCampaigns }) {
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [isSendingOffer, setIsSendingOffer] = useState(false);

  if (!customer) {
    return (
      <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-4">
        <p className="text-slate-500">No customer selected.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold cursor-pointer"
        >
          Return to Customer List
        </button>
      </div>
    );
  }

  const getProductIcon = (productName) => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  const ProductIcon = getProductIcon(customer.recommendedProduct);

  const handleCreateOffer = () => {
    setIsSendingOffer(true);
    setTimeout(() => {
      setIsSendingOffer(false);
      setIsOfferModalOpen(true);
    }, 450);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Breadcrumb & Actions */}
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
            {customer.id}
          </span>
          <button
            onClick={handleCreateOffer}
            disabled={isSendingOffer}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-75"
          >
            {isSendingOffer ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Preparing Offer...</span>
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

      {/* Customer Hero Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs relative overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Avatar & Basic Info */}
          <div className="lg:col-span-4 flex items-start space-x-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-slate-100 border-2 border-slate-200 overflow-hidden shrink-0 shadow-xs">
              {customer.avatar ? (
                <img
                  src={customer.avatar}
                  alt={customer.name}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center font-bold text-slate-700 text-xl">
                  {customer.name.slice(0, 2)}
                </div>
              )}
            </div>

            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                  {customer.name}
                </h2>
                <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {customer.accountStatus}
                </span>
              </div>

              <p className="text-xs font-medium text-slate-600">{customer.occupation}</p>

              <div className="flex flex-col gap-1 text-xs text-slate-500 pt-1">
                <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-400" /> {customer.city}</span>
                <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5 text-slate-400" /> {customer.email}</span>
                <span className="flex items-center gap-1.5"><Phone className="w-3.5 h-3.5 text-slate-400" /> {customer.phone}</span>
              </div>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 rounded-xl p-4 border border-slate-200/80">
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Segment
              </span>
              <p className="text-xs sm:text-sm font-bold text-slate-800 truncate">
                {customer.segment}
              </p>
              <span className="text-[10px] text-blue-600 font-medium">Auto-Clustered</span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Monthly Spending
              </span>
              <p className="text-xs sm:text-sm font-bold text-slate-900">
                {customer.monthlySpending}
              </p>
              <span className="text-[10px] text-emerald-600 font-medium">Top 5% Tier</span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Credit Health
              </span>
              <p className="text-xs sm:text-sm font-bold text-emerald-600">
                {customer.creditScore} CIBIL
              </p>
              <span className="text-[10px] text-slate-500">Tier 1 Prime</span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Liquid Balance
              </span>
              <p className="text-xs sm:text-sm font-bold text-slate-900">
                {customer.savingsBalance}
              </p>
              <span className="text-[10px] text-slate-500">Member since {customer.joinedDate}</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Next Best Offer Highlight Card */}
      <div className="bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Sparkles className="w-48 h-48 text-white" />
        </div>

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Offer & Propensity Meter */}
          <div className="lg:col-span-5 space-y-3">
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-white/15 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-purple-300" />
              <span>AI Next Best Offer (NBO)</span>
            </div>

            <div>
              <span className="text-xs text-purple-200 font-medium">Recommended Product</span>
              <h3 className="text-2xl font-extrabold text-white flex items-center gap-2">
                <ProductIcon className="w-6 h-6 text-purple-300" />
                {customer.recommendedProduct}
              </h3>
            </div>

            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/10 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-purple-200 font-medium">Propensity Score</span>
                <span className="text-emerald-300 font-extrabold text-base">{customer.propensity}%</span>
              </div>
              <div className="w-full bg-black/30 rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-400 to-teal-300 rounded-full transition-all duration-1000"
                  style={{ width: `${customer.propensity}%` }}
                />
              </div>
              <p className="text-[11px] text-purple-200">
                Extremely high conversion probability based on 90-day transaction telemetry.
              </p>
            </div>
          </div>

          {/* Why Recommended Detailed Explanation */}
          <div className="lg:col-span-7 bg-white/10 backdrop-blur-md rounded-xl p-5 border border-white/15 space-y-3">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Why this product was recommended
            </h4>
            <p className="text-xs text-purple-100 leading-relaxed">
              {customer.whyRecommended}
            </p>

            <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-white/10">
              <span className="text-[11px] text-purple-200">
                Model: <strong>Propensity-RFM-NeuralNet v2.4</strong>
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

      {/* 2-Column: Behavioral Patterns & AI Insights vs Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Behavioral Patterns & AI Insights */}
        <div className="lg:col-span-5 space-y-6">
          {/* Behaviour Patterns */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
              <Activity className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Observed Behaviour Patterns</h3>
            </div>

            <div className="space-y-2.5">
              {customer.behaviourPatterns.map((pattern, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-2.5 p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700"
                >
                  <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{pattern}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Insights Card */}
          <div className="bg-gradient-to-br from-purple-50 via-white to-blue-50/60 rounded-xl border border-purple-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center space-x-2 text-purple-700 font-bold text-xs uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span>AI Strategic Insight</span>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed">
              {customer.aiInsights}
            </p>
          </div>
        </div>

        {/* Right Column: Recent Transactions */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col justify-between">
          <div>
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Recent Account Transactions</h3>
                <p className="text-xs text-slate-500">Live feed analyzed for propensity scoring</p>
              </div>
              <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded">
                Past 30 Days
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Merchant / Source</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {customer.recentTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap text-slate-500 font-medium">
                        {tx.date}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap font-bold text-slate-900">
                        {tx.merchant}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">
                          {tx.category}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-bold">
                        <span
                          className={
                            tx.type === 'credit'
                              ? 'text-emerald-600'
                              : 'text-slate-900'
                          }
                        >
                          {tx.type === 'credit' ? `+${tx.amount}` : `-${tx.amount}`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Telemetry updated: 4 mins ago</span>
            <button
              onClick={handleCreateOffer}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Create Offer For {customer.name.split(' ')[0]}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Success Notification Modal */}
      <OfferSuccessModal
        isOpen={isOfferModalOpen}
        onClose={() => setIsOfferModalOpen(false)}
        customer={customer}
        onNavigateCampaigns={onNavigateCampaigns}
      />
    </div>
  );
}
