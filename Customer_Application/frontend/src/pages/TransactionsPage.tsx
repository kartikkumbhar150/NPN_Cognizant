import React, { useEffect, useState } from 'react';
import api from '../services/api';
import './TransactionsPage.css';

interface Tx {
  transactionId: string;
  transactionDate: string;
  transactionType: string;
  transactionMode: string;
  amount: number;
  currency: string;
  merchantName: string;
  transactionDescription: string;
  transactionStatus: string;
  channel: string;
  locationCity: string;
}

interface TxPage {
  content: Tx[];
  totalElements: number;
  totalPages: number;
  page: number;
  size: number;
}

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(n);

const TransactionsPage: React.FC = () => {
  const [data, setData]       = useState<TxPage | null>(null);
  const [page, setPage]       = useState(0);
  const [filter, setFilter]   = useState('');
  const [loading, setLoading] = useState(true);

  const loadPage = (p: number) => {
    setLoading(true);
    api.get(`/api/transactions/me?page=${p}&size=15`)
      .then((r) => { setData(r.data); setPage(p); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPage(0); }, []);

  const filtered = data?.content.filter((tx) =>
    !filter ||
    (tx.merchantName ?? '').toLowerCase().includes(filter.toLowerCase()) ||
    (tx.transactionDescription ?? '').toLowerCase().includes(filter.toLowerCase()) ||
    tx.transactionType.toLowerCase().includes(filter.toLowerCase())
  ) ?? [];

  return (
    <div className="tx-page">
      <div className="tx-header">
        <h1>Transaction History</h1>
        <input
          className="tx-search"
          type="text"
          placeholder="Search by merchant, description..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          id="tx-search"
        />
      </div>

      {loading ? (
        <div className="page-loading"><div className="spinner" /></div>
      ) : (
        <>
          <div className="tx-count">
            Showing {filtered.length} of {data?.totalElements} transactions
          </div>

          <div className="tx-table-wrap">
            <table className="tx-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Merchant</th>
                  <th>Mode</th>
                  <th>City</th>
                  <th>Status</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tx) => (
                  <tr key={tx.transactionId} className={tx.transactionType === 'Credit' ? 'tx-credit' : 'tx-debit'}>
                    <td>{tx.transactionDate}</td>
                    <td className="tx-desc">{tx.transactionDescription || '—'}</td>
                    <td>{tx.merchantName || '—'}</td>
                    <td><span className="mode-badge">{tx.transactionMode}</span></td>
                    <td>{tx.locationCity || '—'}</td>
                    <td>
                      <span className={`status-badge status-${tx.transactionStatus?.toLowerCase()}`}>
                        {tx.transactionStatus}
                      </span>
                    </td>
                    <td className={`tx-amount ${tx.transactionType === 'Credit' ? 'amount-credit' : 'amount-debit'}`}>
                      {tx.transactionType === 'Credit' ? '+' : '-'}{fmt(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="tx-pagination">
            <button
              id="tx-prev"
              onClick={() => loadPage(page - 1)}
              disabled={page === 0}
              className="btn-page"
            >
              ← Prev
            </button>
            <span>Page {page + 1} of {data?.totalPages}</span>
            <button
              id="tx-next"
              onClick={() => loadPage(page + 1)}
              disabled={page >= (data?.totalPages ?? 1) - 1}
              className="btn-page"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default TransactionsPage;
