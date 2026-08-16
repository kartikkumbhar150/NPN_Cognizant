import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Plane,
  CreditCard,
  TrendingUp,
  BadgeDollarSign,
  Briefcase,
  CheckCircle2,
  RefreshCw,
  Edit3,
  Eye,
  Send,
  ArrowRight,
  ArrowLeft,
  Smartphone,
  Mail,
  MessageSquare,
  Users,
  Target,
  Sliders,
  Calendar,
  Layers,
  FileText
} from 'lucide-react';
import CampaignSuccessModal from '../components/CampaignSuccessModal';
import {
  CAMPAIGN_PRODUCTS,
  CAMPAIGN_SEGMENTS,
  PRESET_AI_CONTENT,
  RECENT_CAMPAIGNS_LIST
} from '../data/mockData';

export default function Campaigns({ initialProduct, initialSegment, onNavigateAnalytics }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedProduct, setSelectedProduct] = useState(initialProduct || 'Travel Credit Card');
  const [selectedSegment, setSelectedSegment] = useState(initialSegment || 'Frequent Travellers');
  const [toneOfVoice, setToneOfVoice] = useState('Warm & Rewarding');
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewChannel, setPreviewChannel] = useState('email'); // email, mobile, sms
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);
  const [campaignName, setCampaignName] = useState('Q3 Priority Banking Growth Campaign');

  // Content state
  const [subjectLine, setSubjectLine] = useState('');
  const [messageBody, setMessageBody] = useState('');
  const [ctaButtonText, setCtaButtonText] = useState('');
  const [isEditingContent, setIsEditingContent] = useState(false);
  const [variationIndex, setVariationIndex] = useState(0);

  // Sync initial props if provided
  useEffect(() => {
    if (initialProduct) setSelectedProduct(initialProduct);
    if (initialSegment) setSelectedSegment(initialSegment);
  }, [initialProduct, initialSegment]);

  // Generate content on product / segment change or first load
  const generateAIContent = (index = 0) => {
    setIsGenerating(true);
    setTimeout(() => {
      const productContent = PRESET_AI_CONTENT[selectedProduct] || PRESET_AI_CONTENT['Travel Credit Card'];
      const segmentVariations = productContent[selectedSegment] || productContent.default || productContent[Object.keys(productContent)[0]];
      
      const safeIndex = index % segmentVariations.length;
      const variation = segmentVariations[safeIndex];

      setSubjectLine(variation.subject);
      setMessageBody(variation.body);
      setCtaButtonText(variation.cta || 'Claim Offer');
      setToneOfVoice(variation.tone || 'Professional');
      setVariationIndex(safeIndex);
      setIsGenerating(false);
    }, 400);
  };

  useEffect(() => {
    generateAIContent(0);
  }, [selectedProduct, selectedSegment]);

  const handleRegenerate = () => {
    generateAIContent(variationIndex + 1);
  };

  const getProductIcon = (productName) => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  const steps = [
    { number: 1, title: 'Select Product' },
    { number: 2, title: 'Select Segment' },
    { number: 3, title: 'Generate AI Content' },
    { number: 4, title: 'Preview' },
    { number: 5, title: 'Launch' },
  ];

  const getAudienceCount = () => {
    const seg = CAMPAIGN_SEGMENTS.find((s) => s.name === selectedSegment);
    return seg ? seg.size : 8420;
  };

  const handleLaunchCampaign = () => {
    setIsSuccessModalOpen(true);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Wizard Progress Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6 shadow-xs">
        <div className="flex items-center justify-between max-w-4xl mx-auto relative">
          {/* Background connector line */}
          <div className="absolute top-1/2 left-4 right-4 -translate-y-1/2 h-0.5 bg-slate-200 z-0" />
          <div
            className="absolute top-1/2 left-4 -translate-y-1/2 h-0.5 bg-blue-600 z-0 transition-all duration-300"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 96}%` }}
          />

          {steps.map((step) => {
            const isCompleted = currentStep > step.number;
            const isCurrent = currentStep === step.number;

            return (
              <button
                key={step.number}
                onClick={() => {
                  if (step.number <= currentStep || step.number === currentStep + 1) {
                    setCurrentStep(step.number);
                  }
                }}
                className="relative z-10 flex flex-col items-center group cursor-pointer focus:outline-hidden"
              >
                <div
                  className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold transition-all ${
                    isCompleted
                      ? 'bg-blue-600 text-white shadow-xs'
                      : isCurrent
                      ? 'bg-white border-2 border-blue-600 text-blue-600 ring-4 ring-blue-50'
                      : 'bg-white border-2 border-slate-300 text-slate-400 group-hover:border-slate-400'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="w-4 h-4 sm:w-5 sm:h-5" /> : step.number}
                </div>
                <span
                  className={`mt-2 text-[10px] sm:text-xs font-semibold whitespace-nowrap text-center ${
                    isCurrent
                      ? 'text-blue-600'
                      : isCompleted
                      ? 'text-slate-800'
                      : 'text-slate-400'
                  }`}
                >
                  {step.title}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step Content Container */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        {/* STEP 1: SELECT PRODUCT */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Step 1: Choose Marketing Product</h3>
                <p className="text-xs text-slate-500">Select the banking financial product to promote</p>
              </div>
              <span className="text-xs text-slate-500 font-medium">5 Core Products Configured</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {CAMPAIGN_PRODUCTS.map((prod) => {
                const Icon = getProductIcon(prod.name);
                const isSelected = selectedProduct === prod.name;

                return (
                  <div
                    key={prod.id}
                    onClick={() => setSelectedProduct(prod.name)}
                    className={`rounded-xl border p-5 cursor-pointer transition-all flex flex-col justify-between space-y-3 ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/40 shadow-sm ring-2 ring-blue-500/20'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                            isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                          {prod.badge}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-slate-900">{prod.name}</h4>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                        {prod.description}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-slate-200/60 text-xs">
                      <span className="text-slate-400 font-medium text-[10px] uppercase block">Key USP</span>
                      <p className="font-semibold text-slate-800 text-[11px] truncate">{prod.keyBenefit}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setCurrentStep(2)}
                className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs transition-colors cursor-pointer"
              >
                <span>Continue to Step 2: Select Segment</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: SELECT SEGMENT */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Step 2: Choose Target Audience Segment</h3>
                <p className="text-xs text-slate-500">Selected Product: <strong className="text-blue-600">{selectedProduct}</strong></p>
              </div>
              <span className="text-xs text-slate-500 font-medium">Audience Clustering Active</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {CAMPAIGN_SEGMENTS.map((seg) => {
                const isSelected = selectedSegment === seg.name;

                return (
                  <div
                    key={seg.id}
                    onClick={() => setSelectedSegment(seg.name)}
                    className={`rounded-xl border p-5 cursor-pointer transition-all flex flex-col justify-between space-y-3 ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/40 shadow-sm ring-2 ring-blue-500/20'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-500">Target Segment</span>
                        <span className="text-xs font-extrabold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                          {seg.size.toLocaleString()} accounts
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-900">{seg.name}</h4>
                    </div>

                    <div className="p-2.5 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
                      <div className="flex items-center gap-1.5 text-purple-700 font-semibold text-[11px]">
                        <Sparkles className="w-3 h-3 text-purple-600" />
                        <span>AI Affinity Score</span>
                      </div>
                      <p className="text-slate-700 font-medium">{seg.matchRating}</p>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                      <span>Reach: <strong>{((seg.size / 52480) * 100).toFixed(1)}% of total</strong></span>
                      <span className={isSelected ? 'text-blue-600 font-bold' : ''}>
                        {isSelected ? '✓ Selected' : 'Select'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={() => setCurrentStep(1)}
                className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs transition-colors cursor-pointer"
              >
                <span>Continue to Step 3: Generate AI Content</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: GENERATE AI CONTENT */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="text-base font-bold text-slate-900">Step 3: AI Copy & Messaging Generation</h3>
                </div>
                <p className="text-xs text-slate-500">
                  Targeting <strong className="text-slate-800">{selectedSegment}</strong> for <strong className="text-blue-600">{selectedProduct}</strong>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleRegenerate}
                  disabled={isGenerating}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg text-xs font-bold transition-colors cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                  <span>Regenerate Variation</span>
                </button>
                <button
                  onClick={() => setIsEditingContent(!isEditingContent)}
                  className={`inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                    isEditingContent
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>{isEditingContent ? 'Done Editing' : 'Edit Copy'}</span>
                </button>
              </div>
            </div>

            {/* Campaign Name Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700">Campaign Title</label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 font-semibold focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
              />
            </div>

            {/* AI Generated Content Container */}
            <div className="bg-gradient-to-br from-slate-50 via-purple-50/20 to-blue-50/30 rounded-xl border border-purple-200 p-5 space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-purple-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  Generated AI Pitch Template (Variation #{variationIndex + 1})
                </span>
                <span className="bg-purple-100 text-purple-800 font-semibold px-2.5 py-0.5 rounded-full text-[11px]">
                  Tone: {toneOfVoice}
                </span>
              </div>

              {/* Subject Line */}
              <div className="space-y-1.5 bg-white p-3.5 rounded-lg border border-slate-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                  Subject Line
                </span>
                {isEditingContent ? (
                  <input
                    type="text"
                    value={subjectLine}
                    onChange={(e) => setSubjectLine(e.target.value)}
                    className="w-full px-3 py-1.5 border border-blue-400 rounded text-xs sm:text-sm text-slate-900 font-semibold focus:outline-hidden"
                  />
                ) : (
                  <p className="text-sm font-bold text-slate-900">{subjectLine}</p>
                )}
              </div>

              {/* Message Body */}
              <div className="space-y-1.5 bg-white p-3.5 rounded-lg border border-slate-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                  Message Content
                </span>
                {isEditingContent ? (
                  <textarea
                    rows={6}
                    value={messageBody}
                    onChange={(e) => setMessageBody(e.target.value)}
                    className="w-full px-3 py-1.5 border border-blue-400 rounded text-xs sm:text-sm text-slate-800 leading-relaxed focus:outline-hidden"
                  />
                ) : (
                  <p className="text-xs sm:text-sm text-slate-700 whitespace-pre-line leading-relaxed">
                    {messageBody}
                  </p>
                )}
              </div>

              {/* CTA Button Text */}
              <div className="space-y-1.5 bg-white p-3.5 rounded-lg border border-slate-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                  Call to Action (CTA Button)
                </span>
                {isEditingContent ? (
                  <input
                    type="text"
                    value={ctaButtonText}
                    onChange={(e) => setCtaButtonText(e.target.value)}
                    className="w-full px-3 py-1.5 border border-blue-400 rounded text-xs font-semibold text-slate-900"
                  />
                ) : (
                  <div className="inline-block px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-lg shadow-xs">
                    {ctaButtonText}
                  </div>
                )}
              </div>
            </div>

            {/* Navigation */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={() => setCurrentStep(2)}
                className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setCurrentStep(4)}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs transition-colors cursor-pointer"
                >
                  <Eye className="w-4 h-4" />
                  <span>Preview Multi-Channel Output</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: PREVIEW */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Step 4: Multi-Channel Communication Preview</h3>
                <p className="text-xs text-slate-500">Preview with sample customer data populated (Rahul Sharma)</p>
              </div>

              {/* Channel Selector */}
              <div className="flex items-center bg-slate-100 p-1 rounded-lg">
                <button
                  onClick={() => setPreviewChannel('email')}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    previewChannel === 'email'
                      ? 'bg-white text-blue-600 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Mail className="w-3.5 h-3.5" />
                  <span>Email</span>
                </button>
                <button
                  onClick={() => setPreviewChannel('mobile')}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    previewChannel === 'mobile'
                      ? 'bg-white text-blue-600 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Smartphone className="w-3.5 h-3.5" />
                  <span>Mobile App Push</span>
                </button>
                <button
                  onClick={() => setPreviewChannel('sms')}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    previewChannel === 'sms'
                      ? 'bg-white text-blue-600 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>SMS</span>
                </button>
              </div>
            </div>

            {/* Email Preview */}
            {previewChannel === 'email' && (
              <div className="max-w-2xl mx-auto bg-slate-50 rounded-2xl border border-slate-200 p-6 shadow-sm">
                <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                  {/* Email header bar */}
                  <div className="bg-slate-900 px-6 py-4 text-white flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <span className="font-extrabold text-sm tracking-tight">BankAI Premier</span>
                    </div>
                    <span className="text-[11px] text-slate-400">Retail Banking Group</span>
                  </div>

                  <div className="p-6 space-y-4">
                    <div className="space-y-1 pb-3 border-b border-slate-100">
                      <span className="text-[11px] text-slate-400">Subject</span>
                      <h4 className="text-base font-bold text-slate-900">
                        {subjectLine.replace('{{firstName}}', 'Rahul')}
                      </h4>
                    </div>

                    <div className="text-xs sm:text-sm text-slate-700 whitespace-pre-line leading-relaxed">
                      {messageBody.replace('{{firstName}}', 'Rahul')}
                    </div>

                    <div className="pt-4">
                      <button className="px-6 py-3 bg-blue-600 text-white font-bold text-xs sm:text-sm rounded-lg shadow-sm">
                        {ctaButtonText}
                      </button>
                    </div>

                    <div className="pt-6 border-t border-slate-100 text-[10px] text-slate-400 space-y-1">
                      <p>© 2026 BankAI Enterprise Financial Services. All rights reserved.</p>
                      <p>You received this because you are an active account holder with BankAI.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Mobile App Push Preview */}
            {previewChannel === 'mobile' && (
              <div className="max-w-sm mx-auto bg-slate-900 rounded-3xl p-4 shadow-xl border-4 border-slate-800">
                <div className="w-24 h-4 bg-slate-800 rounded-full mx-auto mb-4" />
                <div className="bg-white/95 backdrop-blur-md rounded-2xl p-4 shadow-lg space-y-2 border border-slate-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1.5">
                      <div className="w-5 h-5 rounded bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                        B
                      </div>
                      <span className="text-xs font-bold text-slate-900">BankAI Mobile</span>
                    </div>
                    <span className="text-[10px] text-slate-400">Now</span>
                  </div>
                  <h5 className="text-xs font-bold text-slate-900 leading-snug">
                    {subjectLine.replace('{{firstName}}', 'Rahul')}
                  </h5>
                  <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-3">
                    {messageBody.replace('{{firstName}}', 'Rahul')}
                  </p>
                </div>
                <div className="mt-8 text-center text-[11px] text-slate-400">
                  Lock Screen Notification Simulation
                </div>
              </div>
            )}

            {/* SMS Preview */}
            {previewChannel === 'sms' && (
              <div className="max-w-sm mx-auto bg-slate-100 rounded-3xl p-5 shadow-md border border-slate-300 space-y-3">
                <div className="text-center text-xs font-bold text-slate-600 pb-2 border-b border-slate-200">
                  SMS: +91 98201 44521
                </div>
                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-2">
                  <p className="text-xs text-slate-800 leading-relaxed">
                    <strong>BankAI:</strong> {subjectLine.replace('{{firstName}}', 'Rahul')}. {messageBody.replace('{{firstName}}', 'Rahul').slice(0, 140)}... Apply now: https://bank.ai/o/8021
                  </p>
                  <span className="text-[9px] text-slate-400 block text-right">10:45 AM</span>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={() => setCurrentStep(3)}
                className="inline-flex items-center space-x-2 px-4 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Edit</span>
              </button>
              <button
                onClick={() => setCurrentStep(5)}
                className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs transition-colors cursor-pointer"
              >
                <span>Proceed to Launch Review</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: LAUNCH */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div className="pb-4 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Step 5: Review & Launch Campaign</h3>
              <p className="text-xs text-slate-500">Confirm target metrics and execute multi-channel dispatch</p>
            </div>

            {/* Executive Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                <span className="text-xs text-slate-500 font-medium">Target Audience</span>
                <h4 className="text-xl font-extrabold text-slate-900">{getAudienceCount().toLocaleString()}</h4>
                <p className="text-[11px] text-blue-600 font-semibold">{selectedSegment}</p>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                <span className="text-xs text-slate-500 font-medium">Projected Conversions</span>
                <h4 className="text-xl font-extrabold text-emerald-600">~{Math.round(getAudienceCount() * 0.052).toLocaleString()}</h4>
                <p className="text-[11px] text-emerald-700 font-semibold">5.2% Est. Conversion Rate</p>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                <span className="text-xs text-slate-500 font-medium">Product Focus</span>
                <h4 className="text-base font-bold text-slate-900 truncate">{selectedProduct}</h4>
                <p className="text-[11px] text-purple-700 font-semibold">AI Next Best Offer</p>
              </div>
            </div>

            {/* Campaign Details Summary */}
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
                  <span className="font-semibold text-slate-800">Email, Mobile In-App, SMS</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500">Cognizant Hackathon Engine</span>
                  <span className="font-bold text-purple-700">BankAI Propensity Rule Set v2.4</span>
                </div>
              </div>
            </div>

            {/* Launch Banner */}
            <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
              <div>
                <h4 className="text-sm font-bold">Ready to dispatch to {getAudienceCount().toLocaleString()} customers?</h4>
                <p className="text-xs text-blue-100 mt-0.5">
                  Automated queues will handle personalized delivery with real-time conversion telemetry.
                </p>
              </div>

              <button
                onClick={handleLaunchCampaign}
                className="inline-flex items-center space-x-2 px-6 py-3 bg-white hover:bg-slate-100 text-slate-900 font-extrabold text-xs sm:text-sm rounded-xl shadow-md transition-all cursor-pointer shrink-0"
              >
                <Send className="w-4 h-4 text-blue-600" />
                <span>Launch Campaign</span>
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

      {/* Historical / Active Campaigns Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Active & Historical Campaigns</h3>
            <p className="text-xs text-slate-500">Recent marketing runs powered by BankAI engine</p>
          </div>
          <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
            18 Total Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Campaign Name</th>
                <th className="px-5 py-3">Target Product</th>
                <th className="px-5 py-3">Segment</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Delivered</th>
                <th className="px-5 py-3">Conversions</th>
                <th className="px-5 py-3">Conv. Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {RECENT_CAMPAIGNS_LIST.map((cmp) => (
                <tr key={cmp.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <p className="font-bold text-slate-900">{cmp.name}</p>
                    <span className="text-[10px] text-slate-400">{cmp.id} • Launched {cmp.launchedDate}</span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap font-medium text-slate-800">
                    {cmp.product}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700">
                      {cmp.segment}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        cmp.status === 'Active'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {cmp.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap font-bold text-slate-900">
                    {cmp.sent.toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap font-bold text-emerald-600">
                    {cmp.conversions}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      {cmp.rate}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Campaign Success Modal */}
      <CampaignSuccessModal
        isOpen={isSuccessModalOpen}
        onClose={() => setIsSuccessModalOpen(false)}
        campaignData={{
          product: selectedProduct,
          segment: selectedSegment,
          audienceCount: getAudienceCount(),
        }}
        onNavigateAnalytics={onNavigateAnalytics}
      />
    </div>
  );
}
