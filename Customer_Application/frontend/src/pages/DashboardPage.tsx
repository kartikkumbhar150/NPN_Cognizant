import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './DashboardPage.css';

interface Summary {
  totalIncome: number;
  totalSpend: number;
  savings: number;
  txCount: number;
  topMerchants: { name: string; amount: number }[];
  monthlySpend: { month: string; amount: number }[];
}

interface Profile {
  firstName: string;
  lastName: string;
  city: string;
  creditScore: number;
  customerSegmentType: string;
  annualIncome: number;
  employmentType: string;
}

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#84cc16'];

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile]   = useState<Profile | null>(null);
  const [summary, setSummary]   = useState<Summary | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/customers/me'),
      api.get('/api/transactions/me/summary'),
    ]).then(([p, s]) => {
      setProfile(p.data);
      setSummary(s.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  const savingsRate = summary && summary.totalIncome > 0
    ? ((summary.savings / summary.totalIncome) * 100).toFixed(1)
    : '0';

  return (
    <div className="dashboard">
      {/* Header greeting */}
      <div className="dash-header">
        <div>
          <h1>Good evening, {profile?.firstName} 👋</h1>
          <p className="dash-sub">{profile?.city} · {profile?.customerSegmentType} · Credit Score: <strong>{profile?.creditScore}</strong></p>
        </div>
        <div className="segment-badge">{profile?.customerSegmentType}</div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card kpi-income">
          <div className="kpi-label">Total Income</div>
          <div className="kpi-value">{fmt(summary?.totalIncome ?? 0)}</div>
          <div className="kpi-sub">{summary?.txCount} transactions</div>
        </div>
        <div className="kpi-card kpi-spend">
          <div className="kpi-label">Total Spend</div>
          <div className="kpi-value">{fmt(summary?.totalSpend ?? 0)}</div>
          <div className="kpi-sub">across all categories</div>
        </div>
        <div className="kpi-card kpi-savings">
          <div className="kpi-label">Net Savings</div>
          <div className="kpi-value">{fmt(summary?.savings ?? 0)}</div>
          <div className="kpi-sub">{savingsRate}% savings rate</div>
        </div>
        <div className="kpi-card kpi-score">
          <div className="kpi-label">Credit Score</div>
          <div className="kpi-value">{profile?.creditScore ?? '—'}</div>
          <div className="kpi-sub">{profile?.employmentType}</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="charts-row">
        {/* Monthly spending */}
        <div className="chart-card">
          <h3>Monthly Spending Trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={summary?.monthlySpend ?? []} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => fmt(v)} />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {summary?.monthlySpend.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top merchants */}
        <div className="chart-card">
          <h3>Top Spending Categories</h3>
          <div className="merchant-list">
            {summary?.topMerchants.map((m, i) => (
              <div key={i} className="merchant-row">
                <div className="merchant-dot" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="merchant-name">{m.name}</span>
                <span className="merchant-amt">{fmt(m.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
