import React, { useState } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Customer360 from './pages/Customer360';
import Segments from './pages/Segments';
import Campaigns from './pages/Campaigns';
import CampaignAnalytics from './pages/CampaignAnalytics';
import Analytics from './pages/Analytics';
import './App.css';

function ProtectedLayout() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // State passed between pages (kept here so it survives route changes)
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [preselectedSegment, setPreselectedSegment] = useState('ALL');
  const [campaignProduct, setCampaignProduct] = useState('Travel Credit Card');
  const [campaignSegment, setCampaignSegment] = useState('Frequent Travellers');
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [selectedCampaignName, setSelectedCampaignName] = useState('');

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Derive currentTab from pathname for sidebar/header active state
  const currentTab = (() => {
    const path = location.pathname;
    if (path.startsWith('/customers/')) return 'customer360';
    if (path.startsWith('/customers')) return 'customers';
    if (path.startsWith('/segments')) return 'segments';
    if (path.startsWith('/campaigns/analytics')) return 'campaign-analytics';
    if (path.startsWith('/campaigns')) return 'campaigns';
    if (path.startsWith('/analytics')) return 'analytics';
    return 'dashboard';
  })();

  const handleSelectCustomer = (customer) => {
    setSelectedCustomer(customer);
    navigate('/customers/360');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectSegmentFilter = (segmentName) => {
    setPreselectedSegment(segmentName);
    navigate('/customers');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartCampaign = (product, segment) => {
    if (product) setCampaignProduct(product);
    if (segment) setCampaignSegment(segment);
    navigate('/campaigns');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleViewCampaignAnalytics = (campaignId, campaignName) => {
    setSelectedCampaignId(campaignId);
    setSelectedCampaignName(campaignName || campaignId);
    navigate('/campaigns/analytics');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigate = (tabId) => {
    const routeMap = {
      dashboard: '/',
      customers: '/customers',
      customer360: '/customers/360',
      segments: '/segments',
      campaigns: '/campaigns',
      'campaign-analytics': '/campaigns/analytics',
      analytics: '/analytics',
    };
    navigate(routeMap[tabId] || '/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col antialiased">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={handleNavigate}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
      />

      <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
        <Header
          currentTab={currentTab}
          onNavigate={handleNavigate}
          onOpenMobileMenu={() => setIsMobileSidebarOpen(true)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Routes>
            <Route path="/" element={
              <Dashboard
                onNavigate={handleNavigate}
                onSelectCustomer={handleSelectCustomer}
                onStartCampaign={handleStartCampaign}
              />
            } />

            <Route path="/customers" element={
              <Customers
                onSelectCustomer={handleSelectCustomer}
                preselectedSegment={preselectedSegment}
                onClearPreselectedSegment={() => setPreselectedSegment('ALL')}
              />
            } />

            <Route path="/customers/360" element={
              selectedCustomer ? (
                <Customer360
                  customer={selectedCustomer}
                  onBack={() => navigate('/customers')}
                  onNavigateCampaigns={() => navigate('/campaigns')}
                />
              ) : (
                <Navigate to="/customers" replace />
              )
            } />

            <Route path="/segments" element={
              <Segments
                onSelectSegmentFilter={handleSelectSegmentFilter}
                onSelectCustomer={handleSelectCustomer}
                onStartCampaign={handleStartCampaign}
              />
            } />

            <Route path="/campaigns" element={
              <Campaigns
                initialProduct={campaignProduct}
                initialSegment={campaignSegment}
                onNavigateAnalytics={() => navigate('/analytics')}
                onViewCampaignAnalytics={handleViewCampaignAnalytics}
              />
            } />

            <Route path="/campaigns/analytics" element={
              selectedCampaignId ? (
                <CampaignAnalytics
                  campaignId={selectedCampaignId}
                  campaignName={selectedCampaignName}
                  onBack={() => navigate('/campaigns')}
                />
              ) : (
                <Navigate to="/campaigns" replace />
              )
            } />

            <Route path="/analytics" element={
              <Analytics
                onNavigateCampaigns={() => navigate('/campaigns')}
              />
            } />

            {/* Catch-all: redirect to dashboard */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function AppShell() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
