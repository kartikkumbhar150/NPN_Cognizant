import React from 'react';
import { CheckCircle2, X, Sparkles, Send, ArrowRight, ShieldCheck, Mail, Smartphone } from 'lucide-react';

export default function OfferSuccessModal({ isOpen, onClose, customer, onNavigateCampaigns }) {
  if (!isOpen || !customer) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header decoration */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="w-12 h-12 rounded-xl bg-white/15 backdrop-blur-md flex items-center justify-center mb-3 text-white border border-white/20">
            <CheckCircle2 className="w-6 h-6 text-emerald-300" />
          </div>

          <h3 className="text-xl font-bold">Personalized Offer Dispatched</h3>
          <p className="text-blue-100 text-xs mt-1">
            BankAI Propensity Rule Triggered & Pre-Approved
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">Recipient</span>
              <span className="text-xs font-bold text-slate-900">{customer.name} ({customer.id})</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">Recommended Offer</span>
              <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">{customer.recommendedProduct}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
              <span className="text-xs text-slate-500 font-medium">AI Propensity Confidence</span>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">{customer.propensity}% Match</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Delivery Channels</span>
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700">
                <span className="inline-flex items-center gap-1"><Mail className="w-3.5 h-3.5 text-blue-600" /> Email</span>
                <span>•</span>
                <span className="inline-flex items-center gap-1"><Smartphone className="w-3.5 h-3.5 text-purple-600" /> Mobile Push</span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl flex items-start space-x-2.5">
            <Sparkles className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
            <p className="text-xs text-purple-900 leading-relaxed">
              <strong className="font-semibold">AI Automated Next Steps:</strong> The customer received a dynamic one-click acceptance link. In-app analytics will track open rate and real-time application conversion.
            </p>
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            >
              Close Window
            </button>
            <button
              onClick={() => {
                onClose();
                if (onNavigateCampaigns) onNavigateCampaigns();
              }}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors cursor-pointer"
            >
              <span>Create Full Campaign</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
