import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Search,
  Users,
  Eye,
  Sparkles,
  Plane,
  CreditCard,
  TrendingUp,
  BadgeDollarSign,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { getCustomers, getSegments } from '../services/api';

const SEGMENT_COLORS = {
  'High Value':          'bg-blue-50 text-blue-700 border-blue-200',
  'Frequent Travellers': 'bg-purple-50 text-purple-700 border-purple-200',
  'Investment Oriented': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  'Loan Ready':          'bg-amber-50 text-amber-700 border-amber-200',
  'Churn Risk':          'bg-rose-50 text-rose-700 border-rose-200',
};

function mapCustomer(c) {
  const annualIncome = c.annual_income || 0;
  const monthlyIncome = Math.round(annualIncome / 12);
  return {
    id:                 c.customer_id,
    name:               `${c.first_name || ''} ${c.last_name || ''}`.trim(),
    email:              c.email || '—',
    city:               c.city || '—',
    segment:            c.customer_segment_type || 'Standard',
    creditScore:        c.credit_score || 0,
    monthlySpending:    `₹${monthlyIncome.toLocaleString('en-IN')}`,
    monthlySpendingRaw: monthlyIncome,
    recommendedProduct: 'Travel Credit Card',
    propensity:         Math.min(95, 65 + Math.floor((c.credit_score || 650) / 25)),
    _raw:               c,
  };
}

const PAGE_SIZE = 50;

export default function Customers({ onSelectCustomer, preselectedSegment, onClearPreselectedSegment }) {
  const [searchTerm, setSearchTerm]         = useState('');
  const [selectedSegment, setSelectedSegment] = useState(preselectedSegment || 'ALL');
  const [customers, setCustomers]           = useState([]);
  const [total, setTotal]                   = useState(0);
  const [page, setPage]                     = useState(0);
  const [loading, setLoading]               = useState(true);
  const [error, setError]                   = useState('');
  const [segmentNames, setSegmentNames]     = useState(['ALL']);
  const debounceRef = useRef(null);

  // Load segments for filter pills
  useEffect(() => {
    getSegments()
      .then((d) => setSegmentNames(['ALL', ...(d.segments || []).map((s) => s.name)]))
      .catch(() => {});
  }, []);

  // Sync preselected segment from parent
  useEffect(() => {
    if (preselectedSegment) setSelectedSegment(preselectedSegment);
  }, [preselectedSegment]);

  const fetchCustomers = useCallback(async (search, segment, pageNum) => {
    setLoading(true);
    setError('');
    try {
      const data = await getCustomers({
        search:  search || undefined,
        limit:   PAGE_SIZE,
        offset:  pageNum * PAGE_SIZE,
      });
      setCustomers((data.customers || []).map(mapCustomer));
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(0);
      fetchCustomers(searchTerm, selectedSegment, 0);
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [searchTerm, selectedSegment, fetchCustomers]);

  const handlePageChange = (newPage) => {
    setPage(newPage);
    fetchCustomers(searchTerm, selectedSegment, newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getProductIcon = (productName = '') => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-6 pb-8">
      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, customer ID, email or city…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600 font-bold"
              >✕</button>
            )}
          </div>

          <div className="flex items-center gap-2.5 text-xs">
            <span className="text-slate-500 font-medium hidden sm:inline">Segment:</span>
            <select
              value={selectedSegment}
              onChange={(e) => {
                setSelectedSegment(e.target.value);
                if (onClearPreselectedSegment) onClearPreselectedSegment();
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {segmentNames.map((seg) => (
                <option key={seg} value={seg}>{seg === 'ALL' ? 'All Segments' : seg}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Quick filter pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs pt-1 border-t border-slate-100">
          <span className="text-slate-400 font-medium mr-1 shrink-0">Quick Filter:</span>
          {segmentNames.map((seg) => (
            <button
              key={seg}
              onClick={() => { setSelectedSegment(seg); if (onClearPreselectedSegment) onClearPreselectedSegment(); }}
              className={`px-3 py-1 rounded-full whitespace-nowrap transition-all font-medium cursor-pointer ${
                selectedSegment === seg
                  ? 'bg-blue-600 text-white font-semibold shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
              }`}
            >
              {seg === 'ALL' ? `All Customers (${total.toLocaleString()})` : seg}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-slate-900">
              Customer Accounts ({total.toLocaleString()})
            </h3>
            <span className="text-xs text-slate-500">Showing page {page + 1} of {totalPages || 1}</span>
          </div>
          {loading && (
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Loading…</span>
            </div>
          )}
        </div>

        {error ? (
          <div className="p-10 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
            <p className="text-sm font-semibold text-red-600">{error}</p>
          </div>
        ) : loading && customers.length === 0 ? (
          <div className="p-10 flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <p className="text-sm text-slate-400">Loading customers…</p>
          </div>
        ) : customers.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Users className="w-10 h-10 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-700">No customers found</h4>
            <button
              onClick={() => { setSearchTerm(''); setSelectedSegment('ALL'); }}
              className="px-4 py-2 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg hover:bg-blue-100 transition-colors cursor-pointer"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto -mx-5 sm:mx-0">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-5 py-3.5">Customer ID</th>
                    <th className="px-5 py-3.5">Name</th>
                    <th className="px-5 py-3.5">Segment</th>
                    <th className="px-5 py-3.5">Monthly Est.</th>
                    <th className="px-5 py-3.5">Credit Score</th>
                    <th className="px-5 py-3.5">Propensity</th>
                    <th className="px-5 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {customers.map((customer) => {
                    const Icon = getProductIcon(customer.recommendedProduct);
                    return (
                      <tr
                        key={customer.id}
                        className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                        onClick={() => onSelectCustomer(customer._raw)}
                      >
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-1 rounded border border-blue-100">
                            {customer.id}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-700 border border-slate-200 shrink-0 text-sm">
                              {customer.name.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{customer.name}</p>
                              <p className="text-[11px] text-slate-500">{customer.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${SEGMENT_COLORS[customer.segment] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                            {customer.segment}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="font-bold text-slate-900 text-sm">{customer.monthlySpending}</span>
                          <span className="text-slate-400 text-[11px] block">/ month est.</span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`font-bold text-sm ${customer.creditScore >= 750 ? 'text-emerald-600' : customer.creditScore >= 650 ? 'text-blue-600' : 'text-amber-600'}`}>
                            {customer.creditScore}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2.5">
                            <div className="w-16 bg-slate-100 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${customer.propensity >= 85 ? 'bg-emerald-500' : customer.propensity >= 75 ? 'bg-blue-500' : 'bg-amber-500'}`}
                                style={{ width: `${customer.propensity}%` }}
                              />
                            </div>
                            <span className={`font-extrabold px-2 py-0.5 rounded text-xs border ${customer.propensity >= 85 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : customer.propensity >= 75 ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                              {customer.propensity}%
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-right">
                          <button
                            onClick={(e) => { e.stopPropagation(); onSelectCustomer(customer._raw); }}
                            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-xs transition-colors shadow-xs cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>View 360°</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-5 py-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total.toLocaleString()} customers
                </span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={page === 0}
                    onClick={() => handlePageChange(page - 1)}
                    className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 text-slate-600" />
                  </button>
                  <span className="text-xs font-semibold text-slate-700 px-2">
                    Page {page + 1} / {totalPages}
                  </span>
                  <button
                    disabled={page >= totalPages - 1}
                    onClick={() => handlePageChange(page + 1)}
                    className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 text-slate-600" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
