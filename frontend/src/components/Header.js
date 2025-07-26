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
    <header className="responsive-header">
      <div className="flex items-center justify-between">
        {/* Left side - Menu button and User info */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          <button
            onClick={onToggleSidebar}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
          
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="bg-primary-100 p-1.5 sm:p-2 rounded-full">
              <User className="w-3 h-3 sm:w-4 sm:h-4 text-primary-600" />
            </div>
            <div className="hidden sm:block">
              <h2 className="font-medium text-gray-900 text-xs sm:text-sm">{user.full_name}</h2>
              <p className="text-xs text-gray-500 capitalize">{user.role}</p>
            </div>
          </div>
        </div>

        {/* Center - Date and Time */}
        <div className="hidden md:flex items-center space-x-2 text-xs sm:text-sm text-gray-600">
          <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
          <span className="hidden lg:inline">{getCurrentDate()}</span>
          <span className="font-medium">{getCurrentTime()}</span>
        </div>

        {/* Right side - Logout */}
        <button
          onClick={onLogout}
          className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
        >
          <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
          <span className="hidden sm:inline text-xs sm:text-sm">Déconnexion</span>
        </button>
      </div>
    </header>
  );
};

export default Header;