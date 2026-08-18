import React, { useState, useEffect, useMemo } from 'react';
import {
  Megaphone, Search, Plus, ChevronRight, CheckCircle2,
  X, Calendar, Target, Sparkles, Send, ArrowRight, ArrowLeft,
  Mail, MessageSquare, Smartphone, Zap, RefreshCw, Eye, Users,
  TrendingUp, BarChart2, AlertTriangle, Brain, Award, Flame,
  Star, Clock, Filter, UserCheck
} from 'lucide-react';
import CampaignSuccessModal from '../components/CampaignSuccessModal';
import {
  getCampaigns, createCampaign, getSegments,
  generateCampaignContent, getCampaignCustomers,
  generatePersonalisedMessage, getCampaignAnalytics, getCampaignInsights
} from '../services/api';

// Age group config for UI
const AGE_GROUP_CONFIG = {
  auto: { label: 'Auto Detect', color: 'bg-slate-100 text-slate-700 border-slate-200', icon: Brain, desc: 'AI detects age from profile' },
  genz: { label: 'Gen Z (≤25)', color: 'bg-pink-50 text-pink-700 border-pink-200', icon: Flame, desc: 'Direct • Humorous • FOMO • Zomato-style' },
  millennial: { label: 'Millennial (26-40)', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Award, desc: '"Congratulations!" opener • Achievement-framing' },
  genx: { label: 'Gen X (41-55)', color: 'bg-blue-50 text-blue-700 border-blue-200', icon: TrendingUp, desc: 'ROI-focused • Trust-based • Professional' },
  boomer: { label: 'Boomer (55+)', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Star, desc: 'Formal • Relationship-based • Branch CTA' },
};

const PRODUCTS = [
  { value: 'Travel Credit Card', label: 'Travel Credit Card (Zero Forex)', segment: 'Frequent Travellers', icon: '✈️' },
  { value: 'Premium Account', label: 'Premium Current Account', segment: 'High Value', icon: '💎' },
  { value: 'SIP / Mutual Fund', label: 'SIP / Mutual Fund', segment: 'Investment Oriented', icon: '📈' },
  { value: 'Personal Loan', label: 'Instant Personal Loan', segment: 'Loan Ready', icon: '💰' },
  { value: 'Credit Card', label: 'Standard Rewards Credit Card', segment: 'Churn Risk', icon: '💳' },
  { value: 'Home Loan', label: 'Home Loan (Low Interest)', segment: 'Home Buyers', icon: '🏠' },
  { value: 'Auto Loan', label: 'Auto Loan (Quick Disbursal)', segment: 'Car Buyers', icon: '🚗' },
  { value: 'Education Loan', label: 'Education Loan', segment: 'Students/Parents', icon: '🎓' },
  { value: 'Life Insurance', label: 'Term Life Insurance', segment: 'Family Planners', icon: '🛡️' },
  { value: 'Health Insurance', label: 'Comprehensive Health Cover', segment: 'Health Conscious', icon: '⚕️' },
  { value: 'Fixed Deposit', label: 'High-Yield Fixed Deposit', segment: 'Conservative Savers', icon: '🏦' },
  { value: 'NPS', label: 'National Pension System', segment: 'Retirement Planners', icon: '👴' },
  { value: 'Salary Account', label: 'Corporate Salary Account', segment: 'Professionals', icon: '💼' },
  { value: 'Gold Loan', label: 'Instant Gold Loan', segment: 'Emergency Credit', icon: '🪙' },
];

const CHANNELS = [
  { id: 'Email', icon: Mail, title: 'Email', desc: 'Rich HTML, personalised subject lines' },
  { id: 'SMS', icon: MessageSquare, title: 'SMS', desc: 'Direct alerts, 85%+ open rate for Gen Z' },
  { id: 'WhatsApp', icon: Smartphone, title: 'WhatsApp', desc: 'High engagement, rich media messaging' },
  { id: 'Push', icon: Zap, title: 'Push Notification', desc: 'Instant app alerts with deep links' },
];

export default function Campaigns({ initialProduct, initialSegment, onNavigateAnalytics, onViewCampaignAnalytics }) {
  // Wizard state
  const [step, setStep] = useState(1);
  const [campaignName, setCampaignName] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(initialProduct || 'Travel Credit Card');
  const [selectedChannel, setSelectedChannel] = useState('Email');
  const [ageStrategy, setAgeStrategy] = useState('auto');

  // NBO customer list
  const [nboCustomers, setNboCustomers] = useState([]);
  const [loadingNbo, setLoadingNbo] = useState(false);
  const [selectedCustomerIds, setSelectedCustomerIds] = useState([]);
  const [customerSearch, setCustomerSearch] = useState('');

  // Content state
  const [previewCustomer, setPreviewCustomer] = useState(null);
  const [previewMsg, setPreviewMsg] = useState(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [generatedSubject, setGeneratedSubject] = useState('');
  const [generatedBody, setGeneratedBody] = useState('');
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [batchError, setBatchError] = useState('');

  // Launch state
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchedCampaign, setLaunchedCampaign] = useState(null);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);

  // Campaigns list
  const [campaignsList, setCampaignsList] = useState([]);
  const [loadingList, setLoadingList] = useState(true);

  // Analytics for launched campaigns
  const [analyticsMap, setAnalyticsMap] = useState({});

  // Insights
  const [insights, setInsights] = useState(null);
  const [loadingInsights, setLoadingInsights] = useState(false);

  // Load campaigns list on mount
  useEffect(() => {
    getCampaigns()
      .then((d) => setCampaignsList(d.campaigns || d || []))
      .catch(console.error)
      .finally(() => setLoadingList(false));
  }, []);

  // Auto-set campaign name when product selected
  useEffect(() => {
    if (!campaignName || campaignName.startsWith('Targeted')) {
      setCampaignName(`Targeted ${selectedProduct} Campaign`);
    }
  }, [selectedProduct]);

  // Pre-fill from initialProduct (coming from Dashboard)
  useEffect(() => {
    if (initialProduct) setSelectedProduct(initialProduct);
    if (initialProduct && !campaignName) {
      setCampaignName(`Targeted ${initialProduct} Campaign`);
    }
  }, [initialProduct]);

  // Step 1 → 2: load NBO customers when moving to step 2
  const handleLoadNboCustomers = async () => {
    setLoadingNbo(true);
    try {
      const data = await getCampaignCustomers(selectedProduct, 200);
      setNboCustomers(data.customers || []);
      setSelectedCustomerIds((data.customers || []).map((c) => c.customer_id));
    } catch (err) {
      console.error(err);
      setNboCustomers([]);
    } finally {
      setLoadingNbo(false);
    }
    setStep(2);
  };

  // Filtered customer list by search
  const filteredCustomers = useMemo(() => {
    if (!customerSearch) return nboCustomers;
    const q = customerSearch.toLowerCase();
    return nboCustomers.filter((c) =>
      c.first_name?.toLowerCase().includes(q) ||
      c.last_name?.toLowerCase().includes(q) ||
      c.customer_id?.toLowerCase().includes(q) ||
      c.city?.toLowerCase().includes(q)
    );
  }, [nboCustomers, customerSearch]);

  const toggleCustomer = (id) => {
    setSelectedCustomerIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selectedCustomerIds.length === filteredCustomers.length) {
      setSelectedCustomerIds([]);
    } else {
      setSelectedCustomerIds(filteredCustomers.map((c) => c.customer_id));
    }
  };

  // Age distribution of selected customers
  const ageDistribution = useMemo(() => {
    const selected = nboCustomers.filter((c) => selectedCustomerIds.includes(c.customer_id));
    const counts = { 'Gen Z (≤25)': 0, 'Millennial (26-40)': 0, 'Gen X (41-55)': 0, 'Boomer (55+)': 0 };
    selected.forEach((c) => {
      const age = c.age || 35;
      if (age <= 25) counts['Gen Z (≤25)']++;
      else if (age <= 40) counts['Millennial (26-40)']++;
      else if (age <= 55) counts['Gen X (41-55)']++;
      else counts['Boomer (55+)']++;
    });
    return counts;
  }, [nboCustomers, selectedCustomerIds]);

  // Step 4: Generate a preview message for the first selected customer
  const handleGeneratePreview = async () => {
    if (selectedCustomerIds.length === 0) return;
    setIsGeneratingPreview(true);
    setBatchError('');
    const firstId = selectedCustomerIds[0];
    const customer = nboCustomers.find((c) => c.customer_id === firstId);
    setPreviewCustomer(customer);
    try {
      const result = await generatePersonalisedMessage({
        customer_id: firstId,
        product: selectedProduct,
        channel: selectedChannel.toLowerCase(),
        age_group: ageStrategy,
      });
      setPreviewMsg(result);
      setGeneratedSubject(result.subject);
      setGeneratedBody(result.body);
    } catch (err) {
      setBatchError(err.message || 'Failed to generate preview message');
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // Step 6: Launch campaign
  const handleLaunchCampaign = async () => {
    setIsLaunching(true);
    try {
      const campaign = await createCampaign({
        customer_id: selectedCustomerIds[0] || 'BATCH_OP',
        customer_name: `${selectedCustomerIds.length} NBO Customers`,
        product: selectedProduct,
        campaign_name: campaignName,
        description: `AI personalised campaign for ${selectedProduct} — ${selectedCustomerIds.length} customers`,
        channel: selectedChannel,
        message_preview: generatedSubject || `${selectedProduct} offer`,
        message_email: selectedChannel === 'Email' ? generatedBody : '',
        message_sms: selectedChannel === 'SMS' ? generatedBody : '',
        age_group_strategy: ageStrategy,
        customer_ids: selectedCustomerIds,
      });
      setLaunchedCampaign(campaign);
      setIsSuccessModalOpen(true);
      const data = await getCampaigns();
      setCampaignsList(data.campaigns || data || []);
    } catch (err) {
      console.error(err);
      alert('Failed to launch campaign: ' + err.message);
    } finally {
      setIsLaunching(false);
    }
  };

  const loadInsights = async () => {
    setLoadingInsights(true);
    try {
      const data = await getCampaignInsights();
      setInsights(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingInsights(false);
    }
  };

  const loadCampaignAnalytics = async (campaignId) => {
    try {
      const data = await getCampaignAnalytics(campaignId);
      setAnalyticsMap((prev) => ({ ...prev, [campaignId]: data }));
    } catch (_) { }
  };

  const productInfo = PRODUCTS.find((p) => p.value === selectedProduct) || PRODUCTS[0];

  const stepLabel = (s) => ['', 'Product', 'Audience', 'Channel', 'Preview', 'Launch'][s];
  const stepClass = (s) => {
    if (s < step) return 'bg-emerald-500 border-emerald-500 text-white';
    if (s === step) return 'bg-blue-600 border-blue-600 text-white ring-4 ring-blue-100';
    return 'bg-white border-slate-300 text-slate-400';
  };

  // ─── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col max-h-[calc(100vh-100px)] mt-6">
      {/* Campaign Wizard Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col overflow-hidden flex-1">
        {/* Step Indicator */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 pt-4 pb-8">
          <div className="flex items-center justify-between max-w-4xl mx-auto relative">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-slate-200 -z-0" />
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-emerald-500 -z-0 transition-all duration-500"
              style={{ width: `${((step - 1) / 4) * 100}%` }}
            />
            {[1, 2, 3, 4, 5].map((s) => (
              <div key={s} className="relative z-10 flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-colors ${stepClass(s)}`}>
                  {s < step ? <CheckCircle2 className="w-4 h-4" /> : s}
                </div>
                <span className={`absolute top-10 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-colors ${s === step ? 'text-blue-700' : 'text-slate-400'}`}>
                  {stepLabel(s)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="px-4 sm:px-5 pb-4 sm:pb-5 pt-2 max-w-5xl mx-auto w-full flex-1 overflow-y-auto">

          {/* ── STEP 1: PRODUCT & NAME ──────────────────────────────────────── */}
          {step === 1 && (
            <div className="flex flex-col gap-4 h-full animate-in fade-in slide-in-from-right-4 duration-300">
              {/* Header + Name row */}
              <div className="flex items-end gap-4 pb-4 pt-2 border-b border-slate-100">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-bold text-slate-900">Step 1: Select Product & Name Campaign</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Choose a product — NBO customers auto-populate in the next step.</p>
                </div>
                <div className="shrink-0 w-72">
                  <label className="block text-[10px] font-bold text-slate-600 mb-1 uppercase tracking-wider">Campaign Name</label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    placeholder="e.g., Q3 Travel Card Blitz"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>
              </div>

              {/* Product grid — 5 per row, 3 rows for 14 items, no scroll */}
              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-2 uppercase tracking-wider">Product to Market</label>
                <div className="grid grid-cols-5 gap-2">
                  {PRODUCTS.map((p) => (
                    <div
                      key={p.value}
                      onClick={() => setSelectedProduct(p.value)}
                      className={`relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl border-2 cursor-pointer transition-all group ${selectedProduct === p.value
                          ? 'border-blue-600 bg-blue-50 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50'
                        }`}
                    >
                      <span className="text-lg shrink-0">{p.icon}</span>
                      <div className="min-w-0 flex-1">
                        <p className={`text-[11px] font-bold leading-tight truncate ${selectedProduct === p.value ? 'text-blue-800' : 'text-slate-800'}`}>{p.label}</p>
                        <p className="text-[9px] text-slate-400 truncate">{p.segment}</p>
                      </div>
                      {selectedProduct === p.value && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-1 flex justify-end mt-auto">
                <button
                  onClick={handleLoadNboCustomers}
                  disabled={!campaignName || loadingNbo}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer text-sm"
                >
                  {loadingNbo ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
                  <span>{loadingNbo ? 'Loading NBO Customers…' : 'Load NBO Customers →'}</span>
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 2: NBO CUSTOMER LIST ───────────────────────────────────── */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Step 2: NBO Customer Audience</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {nboCustomers.length} customers auto-matched as NBO for <strong>{selectedProduct}</strong>. Select who to include.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    {selectedCustomerIds.length} selected
                  </span>
                </div>
              </div>

              {/* Age Distribution */}
              <div className="grid grid-cols-4 gap-2">
                {Object.entries(ageDistribution).map(([label, count]) => {
                  const colors = {
                    'Gen Z (≤25)': 'bg-pink-50 border-pink-200 text-pink-700',
                    'Millennial (26-40)': 'bg-purple-50 border-purple-200 text-purple-700',
                    'Gen X (41-55)': 'bg-blue-50 border-blue-200 text-blue-700',
                    'Boomer (55+)': 'bg-emerald-50 border-emerald-200 text-emerald-700',
                  };
                  return (
                    <div key={label} className={`p-2.5 rounded-lg border text-center ${colors[label] || 'bg-slate-50 border-slate-200 text-slate-700'}`}>
                      <div className="text-lg font-extrabold">{count}</div>
                      <div className="text-[10px] font-semibold leading-tight">{label}</div>
                    </div>
                  );
                })}
              </div>

              {/* Search + Select All */}
              <div className="flex gap-3 items-center">
                <div className="relative flex-1 max-w-xs">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search name, city, ID…"
                    value={customerSearch}
                    onChange={(e) => setCustomerSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                  />
                </div>
                <button
                  onClick={toggleAll}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800 px-3 py-2 rounded-lg bg-blue-50 border border-blue-100 hover:bg-blue-100 transition-colors cursor-pointer"
                >
                  {selectedCustomerIds.length === filteredCustomers.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {/* Customer Table */}
              <div className="border border-slate-200 rounded-xl overflow-hidden max-h-72 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500 sticky top-0">
                    <tr>
                      <th className="px-3 py-2.5 w-8"><input type="checkbox" checked={selectedCustomerIds.length === filteredCustomers.length && filteredCustomers.length > 0} onChange={toggleAll} className="rounded cursor-pointer" /></th>
                      <th className="px-3 py-2.5 text-left">Customer</th>
                      <th className="px-3 py-2.5 text-left">Age / Gen</th>
                      <th className="px-3 py-2.5 text-left">City</th>
                      <th className="px-3 py-2.5 text-right">Credit</th>
                      <th className="px-3 py-2.5 text-right">Propensity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredCustomers.slice(0, 100).map((c) => {
                      const age = c.age || 35;
                      const gen = age <= 25 ? 'Gen Z' : age <= 40 ? 'Millennial' : age <= 55 ? 'Gen X' : 'Boomer';
                      const genColor = age <= 25 ? 'text-pink-600 bg-pink-50' : age <= 40 ? 'text-purple-600 bg-purple-50' : age <= 55 ? 'text-blue-600 bg-blue-50' : 'text-emerald-600 bg-emerald-50';
                      const isSelected = selectedCustomerIds.includes(c.customer_id);
                      return (
                        <tr
                          key={c.customer_id}
                          onClick={() => toggleCustomer(c.customer_id)}
                          className={`cursor-pointer transition-colors hover:bg-slate-50 ${isSelected ? 'bg-blue-50/30' : ''}`}
                        >
                          <td className="px-3 py-2.5 text-center">
                            <input type="checkbox" checked={isSelected} onChange={() => toggleCustomer(c.customer_id)} onClick={(e) => e.stopPropagation()} className="rounded cursor-pointer" />
                          </td>
                          <td className="px-3 py-2.5 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600 shrink-0">
                                {(c.first_name || 'C')[0]}{(c.last_name || '')[0]}
                              </div>
                              <div>
                                <p className="font-bold text-slate-900">{c.first_name} {c.last_name}</p>
                                <p className="text-[10px] text-slate-400">{c.email || c.customer_id}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-2.5 whitespace-nowrap">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${genColor}`}>{gen} • {age}y</span>
                          </td>
                          <td className="px-3 py-2.5 whitespace-nowrap text-slate-600">{c.city}</td>
                          <td className="px-3 py-2.5 whitespace-nowrap text-right font-bold text-slate-700">{c.credit_score}</td>
                          <td className="px-3 py-2.5 whitespace-nowrap text-right">
                            <span className="font-bold text-emerald-600">{c.propensity}%</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="pt-2 flex justify-between">
                <button onClick={() => setStep(1)} className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
                  <ArrowLeft className="w-4 h-4" /><span>Back</span>
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={selectedCustomerIds.length === 0}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <span>Next: Channel →</span><ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 3: CHANNEL & AGE STRATEGY ─────────────────────────────── */}
          {step === 3 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 3: Channel & Age-Generation Strategy</h3>
                <p className="text-xs text-slate-500 mt-1">Choose delivery channel and how AI should tailor messages per age group.</p>
              </div>

              {/* Channel Selection */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Delivery Channel</label>
                <div className="grid grid-cols-4 gap-2">
                  {CHANNELS.map((ch) => (
                    <div
                      key={ch.id}
                      onClick={() => setSelectedChannel(ch.id)}
                      className={`relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl border-2 cursor-pointer transition-all ${selectedChannel === ch.id
                          ? 'border-blue-600 bg-blue-50 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50'
                        }`}
                    >
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${selectedChannel === ch.id ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'
                        }`}>
                        <ch.icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className={`text-[11px] font-bold leading-tight truncate ${selectedChannel === ch.id ? 'text-blue-800' : 'text-slate-800'
                          }`}>{ch.title}</p>
                        <p className="text-[9px] text-slate-400 truncate">{ch.desc}</p>
                      </div>
                      {selectedChannel === ch.id && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
                    </div>
                  ))}
                </div>
              </div>

              {/* Age Strategy */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Age-Generation Marketing Strategy</label>
                <div className="grid grid-cols-4 gap-2">
                  {Object.entries(AGE_GROUP_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    return (
                      <div
                        key={key}
                        onClick={() => setAgeStrategy(key)}
                        className={`relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl border-2 cursor-pointer transition-all ${ageStrategy === key
                            ? 'border-blue-600 bg-blue-50 shadow-sm'
                            : 'border-slate-200 hover:border-blue-200 hover:bg-slate-50'
                          }`}
                      >
                        <span className={`p-1.5 rounded-lg border shrink-0 ${cfg.color}`}><Icon className="w-3.5 h-3.5" /></span>
                        <div className="min-w-0 flex-1">
                          <p className={`text-[11px] font-bold leading-tight truncate ${ageStrategy === key ? 'text-blue-800' : 'text-slate-800'
                            }`}>{cfg.label}</p>
                          <p className="text-[9px] text-slate-400 truncate">{cfg.desc}</p>
                        </div>
                        {ageStrategy === key && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
                      </div>
                    );
                  })}
                </div>
              </div>



              <div className="pt-2 flex justify-between">
                <button onClick={() => setStep(2)} className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
                  <ArrowLeft className="w-4 h-4" /><span>Back</span>
                </button>
                <button
                  onClick={() => { setStep(4); handleGeneratePreview(); }}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl shadow-xs transition-colors cursor-pointer"
                >
                  <Sparkles className="w-4 h-4" /><span>Generate AI Preview →</span>
                </button>
              </div>
            </div>
          )}


          {/* ── STEP 4: PREVIEW & SUMMARY ────────────────────────────────────── */}
          {step === 4 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 4: Campaign Summary</h3>
                <p className="text-xs text-slate-500 mt-1">Review all details before launch.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Target Audience</span>
                  <h4 className="text-2xl font-extrabold text-slate-900">{selectedCustomerIds.length.toLocaleString()}</h4>
                  <p className="text-[11px] text-blue-600 font-semibold">NBO customers for {selectedProduct}</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Estimated Opens</span>
                  <h4 className="text-2xl font-extrabold text-emerald-600">~{Math.round(selectedCustomerIds.length * 0.65).toLocaleString()}</h4>
                  <p className="text-[11px] text-emerald-700 font-semibold">65% est. open rate (personalised)</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Est. Conversions</span>
                  <h4 className="text-2xl font-extrabold text-purple-600">~{Math.round(selectedCustomerIds.length * 0.052).toLocaleString()}</h4>
                  <p className="text-[11px] text-purple-700 font-semibold">5.2% est. conversion rate</p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
                <h4 className="text-sm font-bold text-slate-900">Campaign Spec</h4>
                <div className="space-y-2 text-xs divide-y divide-slate-100">
                  {[
                    ['Campaign Name', campaignName],
                    ['Product', selectedProduct],
                    ['Channel', selectedChannel],
                    ['Age Strategy', AGE_GROUP_CONFIG[ageStrategy]?.label],
                    ['Subject Line', generatedSubject],
                    ['Audience', `${selectedCustomerIds.length} NBO customers`],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between py-1.5">
                      <span className="text-slate-500">{label}</span>
                      <span className="font-bold text-slate-900 text-right max-w-xs truncate">{value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
                <div>
                  <h4 className="text-sm font-bold">Ready to dispatch personalised messages to {selectedCustomerIds.length.toLocaleString()} customers?</h4>
                  <p className="text-xs text-blue-100 mt-0.5">Groq AI will personalise each message individually. Real-time analytics tracking begins immediately.</p>
                </div>
                <button
                  onClick={handleLaunchCampaign}
                  disabled={isLaunching}
                  className="inline-flex items-center justify-center space-x-2 px-6 py-3 bg-white hover:bg-slate-100 text-slate-900 font-extrabold text-sm rounded-xl shadow-md transition-all cursor-pointer shrink-0 disabled:opacity-75"
                >
                  {isLaunching ? <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" /> : <Send className="w-4 h-4 text-blue-600" />}
                  <span>{isLaunching ? 'Launching…' : '🚀 Launch Campaign'}</span>
                </button>
              </div>

              <div className="flex justify-start">
                <button onClick={() => setStep(3)} className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
                  <ArrowLeft className="w-4 h-4" /><span>Back to Channel</span>
                </button>
              </div>
            </div>
          )}

        </div>
      </div>



      <CampaignSuccessModal
        isOpen={isSuccessModalOpen}
        onClose={() => { setIsSuccessModalOpen(false); setStep(1); setCampaignName(''); setGeneratedBody(''); setPreviewMsg(null); setNboCustomers([]); }}
        campaignData={{ product: selectedProduct, segment: productInfo.segment, audienceCount: selectedCustomerIds.length }}
        onNavigateAnalytics={onNavigateAnalytics}
      />
    </div>
  );
}
