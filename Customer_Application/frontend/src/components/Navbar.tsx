import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = [
    { path: '/dashboard',    label: '📊 Dashboard' },
    { path: '/transactions', label: '💳 Transactions' },
    { path: '/insights',     label: '🤖 AI Insights' },
  ];

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="nav-logo">NPN</span>
        <span className="nav-title">Banking</span>
      </div>

      <div className="nav-links">
        {navLinks.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            className={`nav-link ${location.pathname === link.path ? 'nav-link-active' : ''}`}
          >
            {link.label}
          </Link>
        ))}
      </div>

      <div className="nav-user">
        <div className="nav-avatar">{user?.firstName?.[0]}{user?.lastName?.[0]}</div>
        <div className="nav-info">
          <div className="nav-name">{user?.firstName} {user?.lastName}</div>
          <div className="nav-id">{user?.customerId}</div>
        </div>
        <button id="logout-btn" className="btn-logout" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
};

export default Navbar;
