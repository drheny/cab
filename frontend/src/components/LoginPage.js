import React from 'react';
import { Stethoscope, User, Shield } from 'lucide-react';

const LoginPage = ({ onLogin }) => {
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

        {/* Login Options */}
        <div className="space-y-4">
          <button
            onClick={() => onLogin('medecin')}
            className="w-full bg-primary-500 hover:bg-primary-600 text-white font-medium py-4 px-6 rounded-xl transition-colors duration-200 flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Shield className="w-6 h-6" />
            <span className="text-lg">Accès Médecin</span>
          </button>

          <button
            onClick={() => onLogin('secretaire')}
            className="w-full bg-secondary-500 hover:bg-secondary-600 text-white font-medium py-4 px-6 rounded-xl transition-colors duration-200 flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <User className="w-6 h-6" />
            <span className="text-lg">Accès Secrétaire</span>
          </button>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Version 1.0 - Optimisé pour iPad et PC</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;