import React from 'react';
import { Menu, LogOut, User, Clock } from 'lucide-react';

const Header = ({ user, onLogout, onToggleSidebar }) => {
  const getCurrentTime = () => {
    return new Date().toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getCurrentDate = () => {
    return new Date().toLocaleDateString('fr-FR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <header className="pc-header-compact">
      <div className="flex items-center justify-between">
        {/* Left side - Menu button and User info */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 p-2 rounded-full">
              <User className="w-4 h-4 text-primary-600" />
            </div>
            <div>
              <h2 className="font-medium text-gray-900 text-sm">{user.name}</h2>
              <p className="text-xs text-gray-500 capitalize">{user.type}</p>
            </div>
          </div>
        </div>

        {/* Center - Date and Time */}
        <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>{getCurrentDate()}</span>
          <span className="font-medium">{getCurrentTime()}</span>
        </div>

        {/* Right side - Logout */}
        <button
          onClick={onLogout}
          className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline text-sm">Déconnexion</span>
        </button>
      </div>
    </header>
  );
};

export default Header;