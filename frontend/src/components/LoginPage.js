import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Stethoscope, UserCog } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleRoleLogin = async (role) => {
    setIsLoading(true);
    
    try {
      // Simple role-based authentication without password
      const userData = {
        id: role === 'medecin' ? 'doc001' : 'sec001',
        nom: role === 'medecin' ? 'Dr. Médecin' : 'Secrétaire',
        prenom: role === 'medecin' ? 'Principal' : 'Médicale',
        role: role,
        permissions: role === 'medecin' 
          ? ['appointments', 'consultations', 'patients', 'reports', 'ai_room', 'administration']
          : ['appointments', 'patients', 'messages', 'ai_room']
      };

      // Store user data in localStorage
      localStorage.setItem('token', 'auto-login-token');
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('userRole', role);

      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Cabinet Médical</h1>
          <p className="text-gray-600">Choisissez votre rôle pour continuer</p>
        </div>

        {/* Role Selection */}
        <div className="space-y-4">
          {/* Médecin Button */}
          <button
            onClick={() => handleRoleLogin('medecin')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <User className="w-5 h-5" />
            <span>Connexion Médecin</span>
          </button>

          {/* Secrétaire Button */}
          <button
            onClick={() => handleRoleLogin('secretaire')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <UserCog className="w-5 h-5" />
            <span>Connexion Secrétaire</span>
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="mt-4 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Connexion en cours...</span>
          </div>
        )}

        {/* Info */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            Cliquez sur votre rôle pour accéder au système
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;