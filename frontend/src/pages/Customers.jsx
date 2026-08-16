import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Users,
  Eye,
  Sparkles,
  Plane,
  CreditCard,
  TrendingUp,
  BadgeDollarSign,
  Briefcase,
  ArrowUpDown,
  Download,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { CUSTOMERS_LIST, CUSTOMER_SEGMENTS } from '../data/mockData';

export default function Customers({ onSelectCustomer, preselectedSegment, onClearPreselectedSegment }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSegment, setSelectedSegment] = useState(preselectedSegment || 'ALL');
  const [selectedProduct, setSelectedProduct] = useState('ALL');
  const [minPropensity, setMinPropensity] = useState(0);
  const [sortBy, setSortBy] = useState('propensity-desc');

  // Products list for filtering
  const products = [
    'ALL',
    'Travel Credit Card',
    'SIP / Mutual Fund',
    'Personal Loan',
    'Premium Account',
    'Credit Card',
  ];

  const segments = ['ALL', ...CUSTOMER_SEGMENTS.map((s) => s.name)];

  const getProductIcon = (productName) => {
    if (productName.includes('Travel')) return Plane;
    if (productName.includes('SIP') || productName.includes('Mutual')) return TrendingUp;
    if (productName.includes('Loan')) return BadgeDollarSign;
    if (productName.includes('Premium')) return Briefcase;
    return CreditCard;
  };

  const filteredCustomers = useMemo(() => {
    return CUSTOMERS_LIST.filter((customer) => {
      // Search match
      const query = searchTerm.toLowerCase().trim();
      const matchesSearch =
        !query ||
        customer.name.toLowerCase().includes(query) ||
        customer.id.toLowerCase().includes(query) ||
        customer.email.toLowerCase().includes(query) ||
        customer.city.toLowerCase().includes(query) ||
        customer.recommendedProduct.toLowerCase().includes(query);

      // Segment match
      const matchesSegment =
        selectedSegment === 'ALL' || customer.segment === selectedSegment;

      // Product match
      const matchesProduct =
        selectedProduct === 'ALL' || customer.recommendedProduct === selectedProduct;

      // Propensity match
      const matchesPropensity = customer.propensity >= minPropensity;

      return matchesSearch && matchesSegment && matchesProduct && matchesPropensity;
    }).sort((a, b) => {
      if (sortBy === 'propensity-desc') return b.propensity - a.propensity;
      if (sortBy === 'propensity-asc') return a.propensity - b.propensity;
      if (sortBy === 'spend-desc') return b.monthlySpendingRaw - a.monthlySpendingRaw;
      if (sortBy === 'spend-asc') return a.monthlySpendingRaw - b.monthlySpendingRaw;
      if (sortBy === 'name-asc') return a.name.localeCompare(b.name);
      return 0;
    });
  }, [searchTerm, selectedSegment, selectedProduct, minPropensity, sortBy]);

  return (
    <div className="space-y-6 pb-8">
      {/* Top Filter & Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by customer name, ID, email, or city..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Segment Filter */}
            <div className="flex items-center space-x-1.5 text-xs">
              <span className="text-slate-500 font-medium hidden sm:inline">Segment:</span>
              <select
                value={selectedSegment}
                onChange={(e) => {
                  setSelectedSegment(e.target.value);
                  if (onClearPreselectedSegment) onClearPreselectedSegment();
                }}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
              >
                {segments.map((seg) => (
                  <option key={seg} value={seg}>
                    {seg === 'ALL' ? 'All Segments' : seg}
                  </option>
                ))}
              </select>
            </div>

            {/* Product Filter */}
            <div className="flex items-center space-x-1.5 text-xs">
              <span className="text-slate-500 font-medium hidden sm:inline">Product:</span>
              <select
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
              >
                {products.map((prod) => (
                  <option key={prod} value={prod}>
                    {prod === 'ALL' ? 'All Products' : prod}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Filter */}
            <div className="flex items-center space-x-1.5 text-xs">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
              >
                <option value="propensity-desc">Propensity (High → Low)</option>
                <option value="propensity-asc">Propensity (Low → High)</option>
                <option value="spend-desc">Monthly Spend (High → Low)</option>
                <option value="spend-asc">Monthly Spend (Low → High)</option>
                <option value="name-asc">Customer Name (A → Z)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quick Segment Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs pt-1 border-t border-slate-100">
          <span className="text-slate-400 font-medium mr-1 shrink-0">Quick Filter:</span>
          {segments.map((seg) => {
            const isSelected = selectedSegment === seg;
            return (
              <button
                key={seg}
                onClick={() => {
                  setSelectedSegment(seg);
                  if (onClearPreselectedSegment) onClearPreselectedSegment();
                }}
                className={`px-3 py-1 rounded-full whitespace-nowrap transition-all font-medium cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white font-semibold shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                }`}
              >
                {seg === 'ALL' ? 'All Customers (12)' : seg}
              </button>
            );
          })}
        </div>
      </div>

      {/* Customers Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-slate-900">
              Customer Accounts ({filteredCustomers.length})
            </h3>
            <span className="text-xs text-slate-500">
              Showing matching profiles with AI propensity weights
            </span>
          </div>

          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span>Minimum Propensity Score:</span>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={minPropensity}
              onChange={(e) => setMinPropensity(Number(e.target.value))}
              className="w-24 accent-blue-600"
            />
            <span className="font-bold text-slate-800">{minPropensity}%+</span>
          </div>
        </div>

        {filteredCustomers.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Users className="w-10 h-10 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-700">No customers found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No matching profiles found with current filters. Try resetting search or adjusting filters.
            </p>
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedSegment('ALL');
                setSelectedProduct('ALL');
                setMinPropensity(0);
              }}
              className="px-4 py-2 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg hover:bg-blue-100 transition-colors cursor-pointer"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-3.5">Customer ID</th>
                  <th className="px-5 py-3.5">Name</th>
                  <th className="px-5 py-3.5">Segment</th>
                  <th className="px-5 py-3.5">Monthly Spending</th>
                  <th className="px-5 py-3.5">Recommended Product</th>
                  <th className="px-5 py-3.5">Propensity</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {filteredCustomers.map((customer) => {
                  const Icon = getProductIcon(customer.recommendedProduct);
                  const isHighRisk = customer.segment === 'Churn Risk';

                  return (
                    <tr
                      key={customer.id}
                      className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                      onClick={() => onSelectCustomer(customer)}
                    >
                      {/* Customer ID */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-1 rounded border border-blue-100">
                          {customer.id}
                        </span>
                      </td>

                      {/* Name */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-700 border border-slate-200 overflow-hidden shrink-0">
                            {customer.avatar ? (
                              <img
                                src={customer.avatar}
                                alt={customer.name}
                                className="w-full h-full object-cover"
                                referrerPolicy="no-referrer"
                              />
                            ) : (
                              customer.name.slice(0, 2)
                            )}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                              {customer.name}
                            </p>
                            <p className="text-[11px] text-slate-500">{customer.email}</p>
                          </div>
                        </div>
                      </td>

                      {/* Segment */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${
                            customer.segment === 'High Value'
                              ? 'bg-blue-50 text-blue-700 border-blue-200'
                              : customer.segment === 'Frequent Travellers'
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : customer.segment === 'Investment Oriented'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : customer.segment === 'Loan Ready'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          {customer.segment}
                        </span>
                      </td>

                      {/* Monthly Spending */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="font-bold text-slate-900 text-sm">
                          {customer.monthlySpending}
                        </span>
                        <span className="text-slate-400 text-[11px] block">/ month</span>
                      </td>

                      {/* Recommended Product */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center shrink-0 border border-blue-100">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-bold text-slate-800">{customer.recommendedProduct}</p>
                            <span className="text-[10px] text-purple-700 font-medium flex items-center gap-0.5">
                              <Sparkles className="w-2.5 h-2.5 text-purple-500" />
                              Next Best Offer
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Propensity */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-16 bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                customer.propensity >= 85
                                  ? 'bg-emerald-500'
                                  : customer.propensity >= 75
                                  ? 'bg-blue-500'
                                  : 'bg-amber-500'
                              }`}
                              style={{ width: `${customer.propensity}%` }}
                            />
                          </div>
                          <span
                            className={`font-extrabold px-2 py-0.5 rounded text-xs border ${
                              customer.propensity >= 85
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : customer.propensity >= 75
                                ? 'bg-blue-50 text-blue-700 border-blue-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {customer.propensity}%
                          </span>
                        </div>
                      </td>

                      {/* Action */}
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCustomer(customer);
                          }}
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
        )}
      </div>
    </div>
  );
}
