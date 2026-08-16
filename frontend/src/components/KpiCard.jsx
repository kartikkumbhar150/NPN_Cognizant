import React from 'react';
import { ArrowUpRight, ArrowDownRight, Sparkles } from 'lucide-react';

export default function KpiCard({ title, value, change, period, isPositive = true, icon: Icon, color = 'blue', aiBadge = null }) {
  const colorMap = {
    blue: {
      iconBg: 'bg-blue-50 text-blue-600 border-blue-100',
      accent: 'border-l-blue-600',
    },
    purple: {
      iconBg: 'bg-purple-50 text-purple-600 border-purple-100',
      accent: 'border-l-purple-600',
    },
    emerald: {
      iconBg: 'bg-emerald-50 text-emerald-600 border-emerald-100',
      accent: 'border-l-emerald-600',
    },
    amber: {
      iconBg: 'bg-amber-50 text-amber-600 border-amber-100',
      accent: 'border-l-amber-600',
    },
  };

  const selectedColor = colorMap[color] || colorMap.blue;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs transition-all hover:shadow-md hover:border-slate-300">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 tracking-wide uppercase">
          {title}
        </span>
        {Icon && (
          <div className={`w-9 h-9 rounded-lg border flex items-center justify-center ${selectedColor.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {value}
        </h3>
        {aiBadge && (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium bg-purple-50 text-purple-700 border border-purple-200/80 px-2 py-0.5 rounded-full">
            <Sparkles className="w-3 h-3 text-purple-600" />
            {aiBadge}
          </span>
        )}
      </div>

      <div className="mt-2.5 flex items-center space-x-1.5 text-xs">
        <span
          className={`inline-flex items-center font-bold ${
            isPositive ? 'text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded' : 'text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded'
          }`}
        >
          {isPositive ? (
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
          ) : (
            <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
          )}
          {change}
        </span>
        <span className="text-slate-500 font-normal">{period}</span>
      </div>
    </div>
  );
}
