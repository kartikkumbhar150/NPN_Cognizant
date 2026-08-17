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
  auto:       { label: 'Auto Detect',   color: 'bg-slate-100 text-slate-700 border-slate-200',   icon: Brain,   desc: 'AI detects age from profile' },
  genz:       { label: 'Gen Z (≤25)',    color: 'bg-pink-50 text-pink-700 border-pink-200',        icon: Flame,   desc: 'Direct • Humorous • FOMO • Zomato-style' },
  millennial: { label: 'Millennial (26-40)', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Award, desc: '"Congratulations!" opener • Achievement-framing' },
  genx:       { label: 'Gen X (41-55)',  color: 'bg-blue-50 text-blue-700 border-blue-200',        icon: TrendingUp, desc: 'ROI-focused • Trust-based • Professional' },
  boomer:     { label: 'Boomer (55+)',   color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Star, desc: 'Formal • Relationship-based • Branch CTA' },
};

const PRODUCTS = [
  { value: 'Travel Credit Card', label: 'Travel Credit Card (Zero Forex)', segment: 'Frequent Travellers', icon: '✈️' },
  { value: 'Premium Account',    label: 'Premium Current Account',         segment: 'High Value',          icon: '💎' },
  { value: 'SIP / Mutual Fund',  label: 'SIP / Mutual Fund',               segment: 'Investment Oriented', icon: '📈' },
  { value: 'Personal Loan',      label: 'Instant Personal Loan',           segment: 'Loan Ready',          icon: '💰' },
  { value: 'Credit Card',        label: 'Standard Rewards Credit Card',    segment: 'Churn Risk',          icon: '💳' },
];

const CHANNELS = [
  { id: 'Email', icon: Mail,         title: 'Email',           desc: 'Rich HTML, personalised subject lines' },
  { id: 'SMS',   icon: MessageSquare, title: 'SMS',            desc: 'Direct alerts, 85%+ open rate for Gen Z' },
];

export default function Campaigns({ initialProduct, initialSegment, onNavigateAnalytics, onViewCampaignAnalytics }) {
  // Wizard state
  const [step, setStep]   = useState(1);
  const [campaignName, setCampaignName] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(initialProduct || 'Travel Credit Card');
  const [selectedChannel, setSelectedChannel] = useState('Email');
  const [ageStrategy, setAgeStrategy] = useState('auto');

  // NBO customer list
  const [nboCustomers, setNboCustomers]     = useState([]);
  const [loadingNbo, setLoadingNbo]         = useState(false);
  const [selectedCustomerIds, setSelectedCustomerIds] = useState([]);
  const [customerSearch, setCustomerSearch] = useState('');

  // Content state
  const [previewCustomer, setPreviewCustomer] = useState(null);
  const [previewMsg, setPreviewMsg]           = useState(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [generatedSubject, setGeneratedSubject] = useState('');
  const [generatedBody, setGeneratedBody]       = useState('');
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [batchError, setBatchError] = useState('');

  // Launch state
  const [isLaunching, setIsLaunching]     = useState(false);
  const [launchedCampaign, setLaunchedCampaign] = useState(null);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);

  // Campaigns list
  const [campaignsList, setCampaignsList] = useState([]);
  const [loadingList, setLoadingList]     = useState(true);

  // Analytics for launched campaigns
  const [analyticsMap, setAnalyticsMap] = useState({});

  // Insights
  const [insights, setInsights]     = useState(null);
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
    } catch (_) {}
  };

  const productInfo = PRODUCTS.find((p) => p.value === selectedProduct) || PRODUCTS[0];

  const stepLabel = (s) => ['', 'Product', 'Audience', 'Channel', 'AI Draft', 'Preview', 'Launch'][s];
  const stepClass = (s) => {
    if (s < step) return 'bg-emerald-500 border-emerald-500 text-white';
    if (s === step) return 'bg-blue-600 border-blue-600 text-white ring-4 ring-blue-100';
    return 'bg-white border-slate-300 text-slate-400';
  };

  // ─── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 rounded-2xl p-6 sm:p-8 text-white shadow-sm border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-purple-500/20 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-white/15 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>BankAI Personalised Marketing Orchestrator</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">AI Campaign Creator</h2>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed">
            Select a product → NBO customers auto-populate → Groq AI drafts hyper-personalised messages tuned to each customer's <strong>age generation</strong> (Gen Z, Millennial, Gen X, Boomer).
          </p>
        </div>
      </div>

      {/* Campaign Wizard Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Step Indicator */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-5">
          <div className="flex items-center justify-between max-w-4xl mx-auto relative">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-slate-200 -z-0" />
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-emerald-500 -z-0 transition-all duration-500"
              style={{ width: `${((step - 1) / 5) * 100}%` }}
            />
            {[1, 2, 3, 4, 5, 6].map((s) => (
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

        <div className="p-6 sm:p-8 max-w-5xl mx-auto min-h-[420px]">

          {/* ── STEP 1: PRODUCT & NAME ──────────────────────────────────────── */}
          {step === 1 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 1: Select Product & Name Campaign</h3>
                <p className="text-xs text-slate-500 mt-1">Choose the product — NBO customers auto-populate in next step.</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Campaign Name</label>
                <input
                  type="text"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="e.g., Q3 Travel Card Blitz"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Product to Market</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {PRODUCTS.map((p) => (
                    <div
                      key={p.value}
                      onClick={() => setSelectedProduct(p.value)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedProduct === p.value
                          ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                          : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="text-2xl mb-2">{p.icon}</div>
                      <h4 className="text-xs font-bold text-slate-900">{p.label}</h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">Targets: {p.segment}</p>
                      {selectedProduct === p.value && (
                        <div className="mt-2 flex items-center gap-1 text-[10px] text-blue-600 font-bold">
                          <CheckCircle2 className="w-3 h-3" /> Selected
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  onClick={handleLoadNboCustomers}
                  disabled={!campaignName || loadingNbo}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
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
                    'Gen Z (≤25)':        'bg-pink-50 border-pink-200 text-pink-700',
                    'Millennial (26-40)':  'bg-purple-50 border-purple-200 text-purple-700',
                    'Gen X (41-55)':       'bg-blue-50 border-blue-200 text-blue-700',
                    'Boomer (55+)':        'bg-emerald-50 border-emerald-200 text-emerald-700',
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
                <div className="grid grid-cols-2 gap-4 max-w-md">
                  {CHANNELS.map((ch) => (
                    <div
                      key={ch.id}
                      onClick={() => setSelectedChannel(ch.id)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${
                        selectedChannel === ch.id
                          ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${selectedChannel === ch.id ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                        <ch.icon className="w-5 h-5" />
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{ch.title}</h4>
                      <p className="text-[11px] text-slate-500">{ch.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Age Strategy */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Age-Generation Marketing Strategy</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {Object.entries(AGE_GROUP_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    return (
                      <div
                        key={key}
                        onClick={() => setAgeStrategy(key)}
                        className={`p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                          ageStrategy === key
                            ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                            : 'border-slate-200 hover:border-blue-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className={`p-1 rounded-lg border text-xs ${cfg.color}`}><Icon className="w-3.5 h-3.5" /></span>
                          <h4 className="text-xs font-bold text-slate-900">{cfg.label}</h4>
                          {ageStrategy === key && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 ml-auto" />}
                        </div>
                        <p className="text-[11px] text-slate-500">{cfg.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Research callout */}
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4 text-xs space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-purple-800"><Brain className="w-4 h-4" /> Marketing Intelligence</div>
                <p className="text-purple-700">• <strong>Gen Z</strong>: Zomato-style contextual hooks — "Barish ho rahi hai? Zero forex card le lo 🌍" — direct, emoji, FOMO-driven</p>
                <p className="text-purple-700">• <strong>Millennials</strong>: Unstop-style "Congratulations!" opener — customer feels they achieved something, opens immediately</p>
                <p className="text-purple-700">• <strong>Gen X</strong>: ROI-focused, specific numbers, trust signals, family/security angle</p>
                <p className="text-purple-700">• <strong>Boomers</strong>: Formal, relationship-based, personal RM sign-off, branch/phone CTA</p>
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

          {/* ── STEP 4: AI CONTENT PREVIEW ──────────────────────────────────── */}
          {step === 4 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Step 4: AI-Generated Personalised Draft</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Groq AI drafted a {selectedChannel} for the first customer using the <strong>{AGE_GROUP_CONFIG[ageStrategy]?.label}</strong> strategy.
                  </p>
                </div>
                <button
                  onClick={handleGeneratePreview}
                  disabled={isGeneratingPreview}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-sm transition-colors cursor-pointer disabled:opacity-70"
                >
                  {isGeneratingPreview ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  <span>{generatedBody ? 'Regenerate' : 'Generate'}</span>
                </button>
              </div>

              {batchError && <div className="p-3 bg-red-50 text-red-700 text-xs font-semibold rounded-lg border border-red-200">{batchError}</div>}

              {isGeneratingPreview && (
                <div className="h-40 border border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-4 bg-purple-50/30">
                  <div className="flex space-x-2">
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce" />
                  </div>
                  <p className="text-sm font-bold text-purple-900">Groq AI is drafting your {selectedChannel}…</p>
                  <p className="text-xs text-purple-700">Applying {AGE_GROUP_CONFIG[ageStrategy]?.label} strategy for {previewCustomer?.first_name || 'customer'} ({previewCustomer?.age}y)</p>
                </div>
              )}

              {previewMsg && !isGeneratingPreview && (
                <div className="space-y-4 animate-in fade-in duration-500">
                  {/* Customer + strategy badge */}
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-full text-xs font-semibold text-slate-700">
                      <div className="w-5 h-5 rounded-full bg-slate-300 flex items-center justify-center text-[10px] font-bold">{(previewCustomer?.first_name || 'C')[0]}</div>
                      {previewCustomer?.first_name} {previewCustomer?.last_name} • {previewCustomer?.age}y
                    </div>
                    {(() => { const cfg = AGE_GROUP_CONFIG[previewMsg.age_group]; const Icon = cfg?.icon || Brain; return (
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${cfg?.color || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                        <Icon className="w-3.5 h-3.5" />{cfg?.label}
                      </span>
                    ); })()}
                    <span className="text-[11px] text-slate-500 italic">{previewMsg.strategy_used}</span>
                  </div>

                  {selectedChannel === 'Email' ? (
                    /* Email mock */
                    <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm bg-white">
                      <div className="bg-slate-100 px-4 py-2.5 flex items-center justify-between border-b border-slate-200">
                        <div className="flex space-x-1.5">
                          <div className="w-3 h-3 rounded-full bg-rose-400" />
                          <div className="w-3 h-3 rounded-full bg-amber-400" />
                          <div className="w-3 h-3 rounded-full bg-emerald-400" />
                        </div>
                        <span className="text-xs font-semibold text-slate-500 bg-white px-2 py-0.5 rounded shadow-xs">Inbox Preview</span>
                      </div>
                      <div className="p-4 border-b border-slate-100 space-y-1">
                        <p className="text-sm font-bold text-slate-900">{generatedSubject}</p>
                        <p className="text-xs text-slate-500">From: NPN Bank &lt;offers@npnbank.com&gt;</p>
                        <p className="text-xs text-slate-500">To: {previewCustomer?.first_name} {previewCustomer?.last_name} &lt;{previewCustomer?.email}&gt;</p>
                      </div>
                      <div className="p-5 bg-slate-50/50">
                        <textarea
                          rows={7}
                          value={generatedBody}
                          onChange={(e) => setGeneratedBody(e.target.value)}
                          className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none font-serif"
                        />
                        <div className="mt-3 flex justify-center">
                          <div className="px-6 py-2.5 bg-blue-600 text-white font-bold rounded-lg text-sm shadow-sm">Claim {selectedProduct}</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* SMS mock */
                    <div className="max-w-xs mx-auto">
                      <div className="bg-slate-900 rounded-3xl p-4 shadow-xl">
                        <div className="text-center text-slate-400 text-[10px] mb-3">NPN Bank • Now</div>
                        <div className="bg-white rounded-2xl rounded-tl-sm p-4 shadow-sm space-y-2">
                          <p className="text-xs font-bold text-slate-500">📱 {generatedSubject}</p>
                          <textarea
                            rows={5}
                            value={generatedBody}
                            onChange={(e) => setGeneratedBody(e.target.value)}
                            className="w-full text-sm text-slate-800 leading-relaxed focus:outline-none resize-none bg-transparent"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100 rounded-xl">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>This is a preview for <strong>{previewCustomer?.first_name}</strong>. Each customer will receive a uniquely personalised version when you launch.</span>
                  </div>

                  {/* Edit subject */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">{selectedChannel === 'Email' ? 'Subject Line' : 'SMS Header'} (editable)</label>
                    <input
                      type="text"
                      value={generatedSubject}
                      onChange={(e) => setGeneratedSubject(e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    />
                  </div>
                </div>
              )}

              {!previewMsg && !isGeneratingPreview && (
                <div className="h-40 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-3 bg-slate-50">
                  <Sparkles className="w-8 h-8 text-purple-300" />
                  <p className="text-sm font-bold text-slate-500">Click "Generate" to create your personalised draft</p>
                </div>
              )}

              <div className="pt-4 flex justify-between">
                <button onClick={() => setStep(3)} className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
                  <ArrowLeft className="w-4 h-4" /><span>Back</span>
                </button>
                <button
                  onClick={() => setStep(5)}
                  disabled={!generatedBody}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <span>Approve & Continue →</span><ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 5: REVIEW & SUMMARY ────────────────────────────────────── */}
          {step === 5 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 5: Campaign Summary</h3>
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
                <button onClick={() => setStep(4)} className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
                  <ArrowLeft className="w-4 h-4" /><span>Back to Draft</span>
                </button>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ── ACTIVE & HISTORICAL CAMPAIGNS ───────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Active & Historical Campaigns</h3>
            <p className="text-xs text-slate-500">Recent personalised marketing runs with real-time analytics</p>
          </div>
          <div className="flex items-center gap-3">
            {loadingList && <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />}
            <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">{campaignsList.length} Total</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Campaign</th>
                <th className="px-5 py-3">Product</th>
                <th className="px-5 py-3">Channel / Strategy</th>
                <th className="px-5 py-3">Audience</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Analytics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {campaignsList.map((cmp) => {
                const analytics = analyticsMap[cmp.id];
                const stratCfg = AGE_GROUP_CONFIG[cmp.age_group_strategy || 'auto'];
                const StratIcon = stratCfg?.icon || Brain;
                return (
                  <tr key={cmp.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <p className="font-bold text-slate-900">{cmp.campaign_name}</p>
                      <span className="text-[10px] text-slate-400">ID: {cmp.id} • {new Date(cmp.created_at).toLocaleDateString('en-IN')}</span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap font-medium text-slate-800">{cmp.product}</td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-slate-600">{cmp.channel}</span>
                        {stratCfg && <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold border ${stratCfg.color}`}><StratIcon className="w-2.5 h-2.5" />{stratCfg.label}</span>}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap font-medium text-slate-700">{cmp.audience_count?.toLocaleString() || '—'}</td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${cmp.status === 'Active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                        {cmp.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-right">
                      {analytics ? (
                        <div className="text-right space-y-0.5">
                          <p className="text-[11px] font-bold text-slate-800">Open: <span className="text-blue-600">{analytics.rates?.open_rate}%</span> · Conv: <span className="text-emerald-600">{analytics.rates?.overall_conv}%</span></p>
                          {onViewCampaignAnalytics && (
                            <button onClick={() => onViewCampaignAnalytics(cmp.id)} className="text-[10px] text-blue-600 hover:underline cursor-pointer font-semibold">Full Analytics →</button>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => loadCampaignAnalytics(cmp.id)}
                          className="text-[11px] text-blue-600 hover:text-blue-800 font-semibold cursor-pointer hover:underline"
                        >
                          Load Analytics
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {campaignsList.length === 0 && !loadingList && (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-500">No campaigns launched yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── AI SELF-LEARNING INSIGHTS ──────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 rounded-2xl p-6 text-white border border-slate-800">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-300" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">AI Self-Learning Insights</h3>
              <p className="text-xs text-purple-200">Groq analyzes campaign performance and recommends improvements</p>
            </div>
          </div>
          <button
            onClick={loadInsights}
            disabled={loadingInsights}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600/80 hover:bg-purple-600 text-white text-xs font-bold rounded-xl border border-purple-500/50 transition-colors cursor-pointer disabled:opacity-70"
          >
            {loadingInsights ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{insights ? 'Refresh' : 'Generate Insights'}</span>
          </button>
        </div>

        {loadingInsights && (
          <div className="flex items-center gap-3 py-6 justify-center">
            <RefreshCw className="w-5 h-5 text-purple-300 animate-spin" />
            <p className="text-purple-200 text-sm">Groq AI is analyzing campaign performance…</p>
          </div>
        )}

        {insights && !loadingInsights && (
          <div className="space-y-4 animate-in fade-in duration-500">
            <div className="p-3 bg-white/10 rounded-xl border border-white/10 text-sm text-purple-100">{insights.overall_health}</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(insights.insights || []).map((insight, i) => {
                const typeStyle = {
                  warning: 'border-amber-400/30 bg-amber-500/10',
                  success: 'border-emerald-400/30 bg-emerald-500/10',
                  info:    'border-blue-400/30 bg-blue-500/10',
                };
                const typeIcon = { warning: '⚠️', success: '✅', info: '💡' };
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
                <p className="text-xs font-bold text-blue-200 mb-1">🎯 Top Recommendation</p>
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
            <p>Click "Generate Insights" to get AI-powered recommendations based on your campaign performance.</p>
          </div>
        )}
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
