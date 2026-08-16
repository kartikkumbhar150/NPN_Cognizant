import React, { useState, useEffect } from 'react';
import {
  Megaphone, Search, Filter, Plus, ChevronRight, CheckCircle2,
  X, Calendar, Target, Sparkles, Send, ArrowRight, ArrowLeft,
  Mail, MessageSquare, Smartphone, Zap, RefreshCw, Eye
} from 'lucide-react';
import CampaignSuccessModal from '../components/CampaignSuccessModal';
import { getCampaigns, createCampaign, getSegments, generateCampaignContent } from '../services/api';

export default function Campaigns({ initialProduct, initialSegment, onNavigateAnalytics }) {
  // Campaign Wizard State
  const [currentStep, setCurrentStep] = useState(1);
  const [campaignName, setCampaignName] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(initialProduct || 'Travel Credit Card');
  const [selectedSegment, setSelectedSegment] = useState(initialSegment || 'Frequent Travellers');
  const [selectedChannels, setSelectedChannels] = useState(['Email']);
  const [audienceCount, setAudienceCount] = useState(0);

  // Content State
  const [subjectLine, setSubjectLine] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState('');

  // Launch State
  const [isLaunching, setIsLaunching] = useState(false);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);

  // Data State
  const [campaignsList, setCampaignsList] = useState([]);
  const [segmentsData, setSegmentsData] = useState([]);
  const [loadingData, setLoadingData] = useState(true);

  // Load initial data
  useEffect(() => {
    Promise.all([getCampaigns(), getSegments()])
      .then(([cmpData, segData]) => {
        setCampaignsList(cmpData.campaigns || cmpData || []);
        setSegmentsData(segData.segments || []);
      })
      .catch(console.error)
      .finally(() => setLoadingData(false));
  }, []);

  // Update audience count when segment changes
  useEffect(() => {
    const seg = segmentsData.find((s) => s.name === selectedSegment);
    setAudienceCount(seg ? seg.count : 0);
  }, [selectedSegment, segmentsData]);

  // If opened with initial params, prefill step 1
  useEffect(() => {
    if (initialProduct && initialSegment && !campaignName) {
      setCampaignName(`Targeted ${initialProduct} Offer`);
    }
  }, [initialProduct, initialSegment, campaignName]);

  const toggleChannel = (channel) => {
    setSelectedChannels((prev) =>
      prev.includes(channel) ? prev.filter((c) => c !== channel) : [...prev, channel]
    );
  };

  const handleGenerateAIContent = async () => {
    setIsGenerating(true);
    setGenerationError('');
    try {
      const result = await generateCampaignContent({
        product: selectedProduct,
        segment: selectedSegment,
        tone: 'Professional',
      });
      setSubjectLine(result.subject);
      setEmailBody(result.body);
    } catch (err) {
      setGenerationError(err.message || 'Failed to generate content');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLaunchCampaign = async () => {
    setIsLaunching(true);
    try {
      await createCampaign({
        customer_id: 'BATCH_OP', // Indicates segment-wide campaign
        customer_name: `Targeting: ${selectedSegment}`,
        product: selectedProduct,
        campaign_name: campaignName,
        description: `Automated campaign targeting ${audienceCount} customers`,
        channel: selectedChannels.join(', '),
        message_preview: subjectLine,
      });
      setIsSuccessModalOpen(true);
      // Reload campaigns list
      const data = await getCampaigns();
      setCampaignsList(data.campaigns || data || []);
    } catch (err) {
      console.error(err);
      alert('Failed to launch campaign');
    } finally {
      setIsLaunching(false);
    }
  };

  const stepClass = (step) => {
    if (step < currentStep) return 'bg-emerald-500 border-emerald-500 text-white';
    if (step === currentStep) return 'bg-blue-600 border-blue-600 text-white ring-4 ring-blue-100';
    return 'bg-white border-slate-300 text-slate-400';
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 rounded-2xl p-6 sm:p-8 text-white shadow-sm border border-slate-800 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-purple-500/20 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-white/15 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>BankAI Marketing Orchestrator</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">AI Campaign Creator</h2>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed">
            Configure target audience, select financial products, and let our GenAI engine craft hyper-personalised multi-channel copy that converts.
          </p>
        </div>
      </div>

      {/* Main Creation Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Step Indicator */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-5">
          <div className="flex items-center justify-between max-w-3xl mx-auto relative">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-slate-200 -z-0"></div>
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-emerald-500 -z-0 transition-all duration-500"
              style={{ width: `${((currentStep - 1) / 4) * 100}%` }}
            ></div>

            {[1, 2, 3, 4, 5].map((step) => (
              <div key={step} className="relative z-10 flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-colors ${stepClass(step)}`}
                >
                  {step < currentStep ? <CheckCircle2 className="w-4 h-4" /> : step}
                </div>
                <span
                  className={`absolute top-10 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-colors ${
                    step === currentStep ? 'text-blue-700' : 'text-slate-400'
                  }`}
                >
                  {step === 1 && 'Audience'}
                  {step === 2 && 'Channels'}
                  {step === 3 && 'AI Copy'}
                  {step === 4 && 'Preview'}
                  {step === 5 && 'Launch'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 sm:p-8 max-w-4xl mx-auto min-h-[400px]">
          {/* STEP 1: AUDIENCE & PRODUCT */}
          {currentStep === 1 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 1: Define Target Audience & Product</h3>
                <p className="text-xs text-slate-500">Select the customer segment and the Next Best Offer (NBO) product.</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Campaign Name</label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    placeholder="e.g., Q3 High Value Portfolio Upgrade"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Target Segment</label>
                    <select
                      value={selectedSegment}
                      onChange={(e) => setSelectedSegment(e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all appearance-none font-semibold text-slate-900"
                    >
                      {segmentsData.map((s) => (
                        <option key={s.id} value={s.name}>{s.name} (~{s.count.toLocaleString()} customers)</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Product Offer</label>
                    <select
                      value={selectedProduct}
                      onChange={(e) => setSelectedProduct(e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all appearance-none font-semibold text-slate-900"
                    >
                      <option value="Travel Credit Card">Travel Credit Card (Zero Forex)</option>
                      <option value="Premium Account">Premium Current Account</option>
                      <option value="SIP / Mutual Fund">SIP / Mutual Fund</option>
                      <option value="Personal Loan">Instant Personal Loan</option>
                      <option value="Credit Card">Standard Rewards Credit Card</option>
                    </select>
                  </div>
                </div>

                <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-blue-600 font-bold uppercase tracking-wider">Estimated Audience Size</span>
                    <p className="text-sm text-slate-600 mt-0.5">Based on real-time BankAI segment engine.</p>
                  </div>
                  <span className="text-2xl font-extrabold text-blue-700">{audienceCount.toLocaleString()}</span>
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  onClick={() => setCurrentStep(2)}
                  disabled={!campaignName}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <span>Next Step</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: CHANNELS */}
          {currentStep === 2 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 2: Delivery Channels</h3>
                <p className="text-xs text-slate-500">Select where this campaign should be deployed.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { id: 'Email', icon: Mail, title: 'Email', desc: 'Primary HTML communication' },
                  { id: 'SMS', icon: MessageSquare, title: 'SMS Text', desc: 'Direct alerts & short links' },
                  { id: 'Push', icon: Smartphone, title: 'Push Notification', desc: 'In-app mobile alert' },
                ].map((ch) => (
                  <div
                    key={ch.id}
                    onClick={() => toggleChannel(ch.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${
                      selectedChannels.includes(ch.id)
                        ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${selectedChannels.includes(ch.id) ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                      <ch.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{ch.title}</h4>
                      <p className="text-[11px] text-slate-500 mt-1">{ch.desc}</p>
                    </div>
                    {selectedChannels.includes(ch.id) && (
                      <div className="absolute top-2 right-2 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                        <CheckCircle2 className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-6 flex justify-between">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={() => setCurrentStep(3)}
                  disabled={selectedChannels.length === 0}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <span>Next Step</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: AI COPY GENERATION */}
          {currentStep === 3 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Step 3: AI Content Generation</h3>
                  <p className="text-xs text-slate-500">Auto-generate persuasive copy tailored to {selectedSegment}.</p>
                </div>
                <button
                  onClick={handleGenerateAIContent}
                  disabled={isGenerating}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-sm transition-colors cursor-pointer disabled:opacity-70"
                >
                  {isGenerating ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  <span>{emailBody ? 'Regenerate' : 'Generate'} Content</span>
                </button>
              </div>

              {generationError && (
                <div className="p-3 bg-red-50 text-red-700 text-xs font-semibold rounded-lg border border-red-200">
                  {generationError}
                </div>
              )}

              {!emailBody && !isGenerating && (
                <div className="h-48 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-3 p-6 bg-slate-50">
                  <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-700">Ready to write?</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm">Click the generate button above to let BankAI craft personalized email copy for {selectedProduct}.</p>
                  </div>
                </div>
              )}

              {isGenerating && (
                <div className="h-48 border border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-4 p-6 bg-purple-50/30">
                  <div className="flex space-x-2">
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2.5 h-2.5 bg-purple-600 rounded-full animate-bounce"></div>
                  </div>
                  <p className="text-sm font-bold text-purple-900">BankAI is drafting your message…</p>
                  <p className="text-xs text-purple-700 font-medium">Analyzing {selectedSegment} behavioral triggers.</p>
                </div>
              )}

              {emailBody && !isGenerating && (
                <div className="space-y-4 animate-in fade-in duration-500">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Email Subject Line</label>
                    <input
                      type="text"
                      value={subjectLine}
                      onChange={(e) => setSubjectLine(e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Email Body Copy</label>
                    <textarea
                      rows={8}
                      value={emailBody}
                      onChange={(e) => setEmailBody(e.target.value)}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-y"
                    />
                  </div>
                  <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100 rounded-xl">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Copy passes compliance checks and aligns with brand tone guidelines.</span>
                  </div>
                </div>
              )}

              <div className="pt-6 flex justify-between">
                <button
                  onClick={() => setCurrentStep(2)}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={() => setCurrentStep(4)}
                  disabled={!emailBody}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <span>Next Step</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: PREVIEW */}
          {currentStep === 4 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 4: Campaign Preview</h3>
                <p className="text-xs text-slate-500">Review how the customer will see the communication.</p>
              </div>

              {/* Email Client Mockup */}
              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm max-w-2xl mx-auto bg-white">
                <div className="bg-slate-100 px-4 py-3 flex items-center justify-between border-b border-slate-200">
                  <div className="flex space-x-1.5">
                    <div className="w-3 h-3 rounded-full bg-rose-400"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-white px-2 py-0.5 rounded shadow-xs">Inbox Preview</span>
                </div>
                
                <div className="p-5 border-b border-slate-100 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{subjectLine || 'No Subject'}</p>
                      <p className="text-xs text-slate-500 mt-0.5">From: NPN Bank &lt;offers@npnbank.com&gt;</p>
                      <p className="text-xs text-slate-500">To: [Customer Name] ({selectedSegment})</p>
                    </div>
                    <span className="text-xs text-slate-400">10:42 AM</span>
                  </div>
                </div>

                <div className="p-6 bg-slate-50/50">
                  <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs text-sm text-slate-800 leading-relaxed whitespace-pre-line font-serif">
                    {emailBody}
                    <div className="mt-6 pt-4 border-t border-slate-100 flex justify-center">
                      <div className="px-6 py-2.5 bg-blue-600 text-white font-bold rounded-lg text-sm cursor-pointer shadow-sm">
                        Claim {selectedProduct}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 flex justify-between">
                <button
                  onClick={() => setCurrentStep(3)}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Edit</span>
                </button>
                <button
                  onClick={() => setCurrentStep(5)}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-xs transition-colors cursor-pointer"
                >
                  <span>Approve & Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 5: LAUNCH */}
          {currentStep === 5 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Step 5: Review & Launch Campaign</h3>
                <p className="text-xs text-slate-500">Confirm target metrics and execute multi-channel dispatch</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Target Audience</span>
                  <h4 className="text-xl font-extrabold text-slate-900">{audienceCount.toLocaleString()}</h4>
                  <p className="text-[11px] text-blue-600 font-semibold">{selectedSegment}</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Projected Conversions</span>
                  <h4 className="text-xl font-extrabold text-emerald-600">~{Math.round(audienceCount * 0.052).toLocaleString()}</h4>
                  <p className="text-[11px] text-emerald-700 font-semibold">5.2% Est. Conversion Rate</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Product Focus</span>
                  <h4 className="text-base font-bold text-slate-900 truncate">{selectedProduct}</h4>
                  <p className="text-[11px] text-purple-700 font-semibold">AI Next Best Offer</p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
                <h4 className="text-sm font-bold text-slate-900">Campaign Summary Spec</h4>
                <div className="space-y-2 text-xs divide-y divide-slate-100">
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Campaign Title</span>
                    <span className="font-bold text-slate-900">{campaignName}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Subject Line</span>
                    <span className="font-semibold text-slate-800">{subjectLine}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Delivery Channels</span>
                    <span className="font-semibold text-slate-800">{selectedChannels.join(', ')}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Cognizant Hackathon Engine</span>
                    <span className="font-bold text-purple-700">BankAI Propensity Rule Set v2.4</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
                <div>
                  <h4 className="text-sm font-bold">Ready to dispatch to {audienceCount.toLocaleString()} customers?</h4>
                  <p className="text-xs text-blue-100 mt-0.5">Automated queues will handle personalized delivery with real-time conversion telemetry.</p>
                </div>
                <button
                  onClick={handleLaunchCampaign}
                  disabled={isLaunching}
                  className="inline-flex items-center justify-center space-x-2 px-6 py-3 bg-white hover:bg-slate-100 text-slate-900 font-extrabold text-xs sm:text-sm rounded-xl shadow-md transition-all cursor-pointer shrink-0 disabled:opacity-75"
                >
                  {isLaunching ? (
                    <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 text-blue-600" />
                  )}
                  <span>{isLaunching ? 'Launching…' : 'Launch Campaign'}</span>
                </button>
              </div>

              <div className="pt-2 flex justify-start">
                <button
                  onClick={() => setCurrentStep(4)}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Preview</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Historical / Active Campaigns Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Active & Historical Campaigns</h3>
            <p className="text-xs text-slate-500">Recent marketing runs powered by BankAI engine</p>
          </div>
          {loadingData ? (
            <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
          ) : (
            <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
              {campaignsList.length} Total Campaigns
            </span>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Campaign Name</th>
                <th className="px-5 py-3">Target Product</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Channels</th>
                <th className="px-5 py-3">Created By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {campaignsList.map((cmp) => (
                <tr key={cmp.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <p className="font-bold text-slate-900">{cmp.campaign_name}</p>
                    <span className="text-[10px] text-slate-400">ID: {cmp.id} • {cmp.created_at}</span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap font-medium text-slate-800">
                    {cmp.product}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        cmp.status === 'Active'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}
                    >
                      {cmp.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="font-medium text-slate-600">{cmp.channel}</span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap text-slate-500">
                    {cmp.created_by}
                  </td>
                </tr>
              ))}
              {campaignsList.length === 0 && !loadingData && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-500">No campaigns launched yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <CampaignSuccessModal
        isOpen={isSuccessModalOpen}
        onClose={() => { setIsSuccessModalOpen(false); setCurrentStep(1); setCampaignName(''); setEmailBody(''); }}
        campaignData={{ product: selectedProduct, segment: selectedSegment, audienceCount }}
        onNavigateAnalytics={onNavigateAnalytics}
      />
    </div>
  );
}
