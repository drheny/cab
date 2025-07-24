import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import axios from 'axios';

// Components
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import PatientsList from './components/PatientsList';
import Calendar from './components/Calendar';
import AIRoom from './components/AIRoom';
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
    // AUTO-LOGIN AS DOCTOR - BYPASS AUTHENTICATION
    const autoLoginAsDoctor = () => {
      const doctorUser = {
        id: 'auto-doctor-id',
        username: 'medecin',
        email: '',
        full_name: 'Dr Heni Dridi',
        role: 'medecin',
        permissions: {
          dashboard: true,
          patients: true,
          calendar: true,
          messages: true,
          billing: true,
          consultation: true,
          administration: true,
          create_appointment: true,
          edit_appointment: true,
          delete_appointment: true,
          view_payments: true,
          edit_payments: true,
          delete_payments: true,
          export_data: true,
          reset_data: true,
          manage_users: true,
          consultation_read_only: false
        },
        last_login: new Date().toISOString()
      };
      
      // Set mock token for API calls
      const mockToken = 'auto-login-token';
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('user', JSON.stringify(doctorUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;
      
      setUser(doctorUser);
      console.log('🚀 AUTO-LOGIN: Logged in as doctor');
    };

    // Check if user is already logged in or auto-login
    const token = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        setUser(userData);
        console.log('🔄 RESTORED: Previous login session');
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        autoLoginAsDoctor();
      }
    } else {
      // Auto-login as doctor
      autoLoginAsDoctor();
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

  useEffect(() => {
    // Load phone messages count for sidebar badge
    const loadPhoneMessagesCount = async () => {
      if (!user) return;
      
      try {
        const response = await axios.get('/api/phone-messages/stats');
        setPhoneMessagesCount(response.data.nouveau || 0);
      } catch (error) {
        console.error('Error loading phone messages count:', error);
      }
    };

    loadPhoneMessagesCount();
    
    // Update count every 30 seconds
    const interval = setInterval(loadPhoneMessagesCount, 30000);
    
    return () => clearInterval(interval);
  }, [user]);

  const handleLogin = (userData, token) => {
    // Set axios default authorization header for future requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    setUser(userData);
  };

  const handleLogout = () => {
    // Clear token and user data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
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
    return <LoginPage onLogin={handleLogin} />;
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
          phoneMessagesCount={phoneMessagesCount}
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
              <Route path="/ai-room" element={<AIRoom user={user} />} />
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