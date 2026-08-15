import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const [customerId, setCustomerId] = useState('');
  const [password, setPassword]     = useState('');
  const [error, setError]           = useState('');
  const [loading, setLoading]       = useState(false);
  const { login } = useAuth();
  const navigate  = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/api/auth/login', { customerId, password });
      login(data.token, {
        customerId:           data.customerId,
        firstName:            data.firstName,
        lastName:             data.lastName,
        email:                data.email,
        customerSegmentType:  data.customerSegmentType,
      });
      navigate('/dashboard');
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK') {
        setError('Network Error: Cannot connect to the backend server (ensure it is running on port 8080).');
      } else {
        setError(err.response?.data?.error || 'Login failed. Please check your credentials (ensure both are uppercase).');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root">
      <div className="login-left">
        <div className="login-brand">
          <div className="login-logo">NPN</div>
          <h1>Banking Portal</h1>
          <p>Your complete financial intelligence platform</p>
        </div>
        <div className="login-features">
          <div className="feature-item">📊 Real-time spending insights</div>
          <div className="feature-item">🤖 AI-powered recommendations</div>
          <div className="feature-item">🛡️ Financial gap detection</div>
          <div className="feature-item">💳 Personalised product offers</div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-card">
          <h2>Welcome back</h2>
          <p className="login-subtitle">Sign in to your account</p>

          <form onSubmit={handleSubmit} id="login-form">
            <div className="form-group">
              <label htmlFor="customerId">Customer ID</label>
              <input
                id="customerId"
                type="text"
                placeholder="e.g. CUST00125"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value.toUpperCase())}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Your password (e.g. CUST00125)"
                value={password}
                onChange={(e) => setPassword(e.target.value.toUpperCase())}
                required
              />
            </div>

            {error && <div className="login-error">{error}</div>}

            <button
              id="login-submit"
              type="submit"
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="login-hint">
            💡 Demo: use your Customer ID as both username and password
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
