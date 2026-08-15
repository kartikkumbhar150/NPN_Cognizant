import React, { useState } from 'react';
import api from '../services/api';
import { RadialBarChart, RadialBar, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import './InsightsPage.css';

interface Gap {
  code: string;
  severity: number;
  title: string;
  insight: string;
  products: string[];
}

interface Analysis {
  health_score: { score: number; grade: string; breakdown: Record<string, number> };
  income_profile: { monthly_avg_income: number; monthly_avg_savings: number; savings_rate_pct: number; months_observed: number };
  spending_breakdown: Record<string, { total: number; monthly_avg: number; pct_of_income: number }>;
  gaps: Gap[];
  next_best_offer: { product: string; propensity: string; reasons: string[]; gap_code: string };
  marketing_message: string;
}

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const SEVERITY_COLOR: Record<number, string> = {
  9: '#ef4444', 8: '#f97316', 7: '#f59e0b', 6: '#eab308', 5: '#84cc16',
};

const PIE_COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#84cc16'];

const InsightsPage: React.FC = () => {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const runAnalysis = () => {
    setLoading(true);
    setError('');
    api.post('/api/ai/analyse')
      .then((r) => setAnalysis(r.data))
      .catch((e) => setError(e.response?.data?.error || 'Analysis failed'))
      .finally(() => setLoading(false));
  };

  const spendingData = analysis
    ? Object.entries(analysis.spending_breakdown)
        .map(([cat, v]) => ({ name: cat, value: Math.round(v.monthly_avg) }))
        .sort((a, b) => b.value - a.value)
    : [];

  const score = analysis?.health_score.score ?? 0;
  const scoreColor = score >= 80 ? '#10b981' : score >= 65 ? '#6366f1' : score >= 45 ? '#f59e0b' : '#ef4444';

  return (
    <div className="insights-page">
      <div className="insights-header">
        <div>
          <h1>AI Financial Insights</h1>
          <p>Deep analysis of your spending, gaps, and personalised product recommendations</p>
        </div>
        <button
          id="run-analysis"
          className="btn-analyse"
          onClick={runAnalysis}
          disabled={loading}
        >
          {loading ? '🔄 Analysing...' : '🤖 Run AI Analysis'}
        </button>
      </div>

      {error && <div className="insights-error">{error}</div>}

      {!analysis && !loading && (
        <div className="insights-empty">
          <div className="empty-icon">🤖</div>
          <h3>Ready to analyse your finances</h3>
          <p>Click "Run AI Analysis" to get your personalised financial health report</p>
        </div>
      )}

      {analysis && (
        <div className="insights-content">

          {/* Health Score + Income */}
          <div className="score-row">
            <div className="score-card">
              <h3>Financial Health Score</h3>
              <div className="score-circle" style={{ '--score-color': scoreColor } as React.CSSProperties}>
                <div className="score-num" style={{ color: scoreColor }}>{score}</div>
                <div className="score-label">{analysis.health_score.grade}</div>
              </div>
              <div className="score-breakdown">
                {Object.entries(analysis.health_score.breakdown).map(([k, v]) => (
                  <div key={k} className="score-row-item">
                    <span>{k.replace(/_/g, ' ')}</span>
                    <div className="score-bar-wrap">
                      <div className="score-bar" style={{ width: `${(v / 30) * 100}%`, background: scoreColor }} />
                    </div>
                    <span>{v}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="income-card">
              <h3>Income & Savings</h3>
              <div className="income-stat">
                <div className="income-label">Monthly Income</div>
                <div className="income-val">{fmt(analysis.income_profile.monthly_avg_income)}</div>
              </div>
              <div className="income-stat">
                <div className="income-label">Monthly Savings</div>
                <div className="income-val">{fmt(analysis.income_profile.monthly_avg_savings)}</div>
              </div>
              <div className="savings-rate-bar">
                <div className="savings-rate-fill" style={{
                  width: `${Math.min(analysis.income_profile.savings_rate_pct, 100)}%`,
                  background: scoreColor
                }} />
              </div>
              <p className="savings-rate-label">{analysis.income_profile.savings_rate_pct}% savings rate</p>
            </div>
          </div>

          {/* Spending Pie + Gaps */}
          <div className="breakdown-row">
            <div className="pie-card">
              <h3>Spending Breakdown</h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={spendingData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {spendingData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v: number) => fmt(v)} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="gaps-card">
              <h3>Financial Gaps Detected</h3>
              {analysis.gaps.length === 0 ? (
                <p className="no-gaps">🎉 No significant financial gaps detected!</p>
              ) : (
                analysis.gaps.map((gap, i) => (
                  <div key={i} className="gap-item" style={{ borderLeft: `4px solid ${SEVERITY_COLOR[gap.severity] ?? '#6366f1'}` }}>
                    <div className="gap-title">{gap.title}</div>
                    <div className="gap-insight">{gap.insight}</div>
                    <div className="gap-products">
                      {gap.products.map((p, j) => <span key={j} className="product-tag">{p}</span>)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Next Best Offer */}
          <div className="nbo-card">
            <div className="nbo-left">
              <div className="nbo-tag">🎯 Next Best Offer</div>
              <h2>{analysis.next_best_offer.product}</h2>
              <div className="nbo-propensity">Recommendation Strength: <strong>{analysis.next_best_offer.propensity}</strong></div>
              <ul className="nbo-reasons">
                {analysis.next_best_offer.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
            <button id="nbo-apply" className="btn-apply">Apply Now →</button>
          </div>

          {/* AI Marketing Message */}
          <div className="marketing-card">
            <h3>🤖 AI Generated Message</h3>
            <pre className="marketing-message">{analysis.marketing_message}</pre>
          </div>

        </div>
      )}
    </div>
  );
};

export default InsightsPage;
