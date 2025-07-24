import React, { useState } from 'react';
import { Stethoscope, User, Shield, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const LoginPage = ({ onLogin }) => {
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!loginForm.username || !loginForm.password) {
      toast.error('Veuillez saisir votre nom d\'utilisateur et mot de passe');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username: loginForm.username,
        password: loginForm.password
      });

      const { access_token, user } = response.data;
      
      // Store token and user data
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      toast.success(`Bienvenue ${user.full_name}`);
      onLogin(user, access_token);
      
    } catch (error) {
      console.error('Login error:', error);
      if (error.response?.status === 401) {
        toast.error('Nom d\'utilisateur ou mot de passe incorrect');
      } else {
        toast.error('Erreur de connexion. Veuillez réessayer.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (userType) => {
    const credentials = userType === 'medecin' 
      ? { username: 'medecin', password: 'medecin123' }
      : { username: 'secretaire', password: 'secretaire123' };
    
    setLoginForm(credentials);
    // Auto-submit after setting credentials
    setTimeout(() => {
      handleLogin({ preventDefault: () => {} });
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-primary-500 p-3 rounded-full">
              <Stethoscope className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Cabinet Médical
          </h1>
          <p className="text-gray-600">
            Système de gestion pédiatrique
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              value={loginForm.username}
              onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Saisissez votre nom d'utilisateur"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mot de passe
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={loginForm.password}
                onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Saisissez votre mot de passe"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-500 hover:bg-primary-600 disabled:bg-primary-300 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-gradient-to-br from-primary-50 to-secondary-50 px-2 text-gray-500">
              Ou connexion rapide
            </span>
          </div>
        </div>

        {/* Quick Login Options */}
        <div className="space-y-3">
          <button
            onClick={() => handleQuickLogin('medecin')}
            disabled={loading}
            className="w-full bg-primary-500 hover:bg-primary-600 disabled:bg-primary-300 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-3"
          >
            <Shield className="w-5 h-5" />
            <span>Accès Médecin</span>
          </button>

          <button
            onClick={() => handleQuickLogin('secretaire')}
            disabled={loading}
            className="w-full bg-secondary-500 hover:bg-secondary-600 disabled:bg-secondary-300 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-3"
          >
            <User className="w-5 h-5" />
            <span>Accès Secrétaire</span>
          </button>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Version 2.0 - Authentification sécurisée</p>
          <p className="mt-1">Comptes par défaut: medecin/medecin123 | secretaire/secretaire123</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;