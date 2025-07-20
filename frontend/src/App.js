import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import axios from 'axios';

// Components
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import PatientsList from './components/PatientsList';
import Calendar from './components/Calendar';
import Messages from './components/Messages';
import Consultation from './components/Consultation';
import Billing from './components/Billing';
import Administration from './components/Administration';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
axios.defaults.baseURL = API_BASE_URL;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [phoneMessagesCount, setPhoneMessagesCount] = useState(0);

  useEffect(() => {
    // Check if user is logged in (stored in localStorage)
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    // Initialize demo data when app loads
    const initDemoData = async () => {
      try {
        await axios.get('/api/init-demo');
        console.log('Demo data initialized');
      } catch (error) {
        console.error('Error initializing demo data:', error);
      }
    };
    
    initDemoData();
  }, []);

  const handleLogin = (userType) => {
    const userData = {
      type: userType,
      name: userType === 'medecin' ? 'Dr Heni Dridi' : 'Secrétaire',
      permissions: userType === 'medecin' ? ['all'] : ['patients', 'appointments', 'consultations']
    };
    
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <LoginPage onLogin={handleLogin} />
        <Toaster position="top-right" />
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Toaster position="top-right" />
        
        {/* Sidebar */}
        <Sidebar 
          user={user} 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)} 
        />
        
        {/* Main Content */}
        <div className="responsive-main-content">
          <Header 
            user={user} 
            onLogout={handleLogout} 
            onToggleSidebar={toggleSidebar}
          />
          
          <main className="responsive-padding max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard user={user} />} />
              <Route path="/patients" element={<PatientsList user={user} />} />
              <Route path="/calendar" element={<Calendar user={user} />} />
              <Route path="/messages" element={<Messages user={user} />} />
              <Route path="/consultation" element={<Consultation user={user} />} />
              <Route path="/billing" element={<Billing user={user} />} />
              <Route path="/administration" element={<Administration user={user} />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;