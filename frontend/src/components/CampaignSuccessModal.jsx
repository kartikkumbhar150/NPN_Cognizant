import React from 'react';
import { CheckCircle2, X, Sparkles, Send, Megaphone, Users, Calendar, ArrowRight, BarChart2 } from 'lucide-react';

export default function CampaignSuccessModal({ isOpen, onClose, campaignData, onNavigateAnalytics }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-blue-600 px-6 py-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="w-12 h-12 rounded-xl bg-white/15 backdrop-blur-md flex items-center justify-center mb-3 text-white border border-white/20">
            <CheckCircle2 className="w-6 h-6 text-emerald-200" />
          </div>

          <h3 className="text-xl font-bold">Campaign launched successfully</h3>
          <p className="text-emerald-100 text-xs mt-1">
            Your campaign is ready for delivery.
          </p>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">Campaign Target Product</span>
              <span className="text-xs font-bold text-slate-900">{campaignData?.product || 'Travel Credit Card'}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">Target Segment Audience</span>
              <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                {campaignData?.segment || 'Frequent Travellers'} ({campaignData?.audienceCount?.toLocaleString() || '8,420'} customers)
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">Estimated Conversion Lift</span>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                +4.8% — 5.6% Conversion Rate
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Execution Engine</span>
              <span className="text-xs font-semibold text-purple-700 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                Prism Smart Batch Dispatcher
              </span>
            </div>
          </div>

          <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 leading-relaxed">
            <span className="font-semibold text-blue-950">Queue Confirmation:</span> 
            {" "}Audience segments have been synchronized with the core marketing delivery queue. Open telemetry, CTR tracking, and downstream conversion analytics are now live.
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            >
              Close
            </button>
            <button
              onClick={() => {
                onClose();
                if (onNavigateAnalytics) onNavigateAnalytics();
              }}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors cursor-pointer"
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>View Live Analytics</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
