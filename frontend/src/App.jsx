import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Customer360 from './pages/Customer360';
import Segments from './pages/Segments';
import Campaigns from './pages/Campaigns';
import Analytics from './pages/Analytics';
import './App.css';

function AppShell() {
  const { isAuthenticated } = useAuth();
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [preselectedSegment, setPreselectedSegment] = useState('ALL');
  const [campaignProduct, setCampaignProduct] = useState('Travel Credit Card');
  const [campaignSegment, setCampaignSegment] = useState('Frequent Travellers');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  if (!isAuthenticated) {
    return <Login />;
  }

  // Navigate to customer 360 page
  const handleSelectCustomer = (customer) => {
    setSelectedCustomer(customer);
    setCurrentTab('customer360');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Filter customers by segment from Segments page
  const handleSelectSegmentFilter = (segmentName) => {
    setPreselectedSegment(segmentName);
    setCurrentTab('customers');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Launch campaign from Opportunities or Segments
  const handleStartCampaign = (product, segment) => {
    if (product) setCampaignProduct(product);
    if (segment) setCampaignSegment(segment);
    setCurrentTab('campaigns');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Tab navigation
  const handleNavigate = (tabId) => {
    setCurrentTab(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col antialiased">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={handleNavigate}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
      />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
        {/* Top Sticky Header */}
        <Header
          currentTab={currentTab}
          onNavigate={handleNavigate}
          onOpenMobileMenu={() => setIsMobileSidebarOpen(true)}
        />

        {/* Dynamic Page Views */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {currentTab === 'dashboard' && (
            <Dashboard
              onNavigate={handleNavigate}
              onSelectCustomer={handleSelectCustomer}
              onStartCampaign={handleStartCampaign}
            />
          )}

          {currentTab === 'customers' && (
            <Customers
              onSelectCustomer={handleSelectCustomer}
              preselectedSegment={preselectedSegment}
              onClearPreselectedSegment={() => setPreselectedSegment('ALL')}
            />
          )}

          {currentTab === 'customer360' && (
            <Customer360
              customer={selectedCustomer}
              onBack={() => handleNavigate('customers')}
              onNavigateCampaigns={() => handleNavigate('campaigns')}
            />
          )}

          {currentTab === 'segments' && (
            <Segments
              onSelectSegmentFilter={handleSelectSegmentFilter}
              onSelectCustomer={handleSelectCustomer}
              onStartCampaign={handleStartCampaign}
            />
          )}

          {currentTab === 'campaigns' && (
            <Campaigns
              initialProduct={campaignProduct}
              initialSegment={campaignSegment}
              onNavigateAnalytics={() => handleNavigate('analytics')}
            />
          )}

          {currentTab === 'analytics' && (
            <Analytics
              onNavigateCampaigns={() => handleNavigate('campaigns')}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
