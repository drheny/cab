import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Users, 
  Calendar, 
  Stethoscope, 
  CreditCard, 
  Settings,
  X,
  MessageSquare 
} from 'lucide-react';

const Sidebar = ({ user, isOpen, onClose, phoneMessagesCount = 0 }) => {
  const location = useLocation();

  const menuItems = [
    { id: 'dashboard', label: 'Tableau de bord', icon: Home, path: '/dashboard', permission: 'all' },
    { id: 'patients', label: 'Patients', icon: Users, path: '/patients', permission: 'patients' },
    { id: 'calendar', label: 'Calendrier', icon: Calendar, path: '/calendar', permission: 'appointments' },
    { id: 'messages', label: 'Messages', icon: MessageSquare, path: '/messages', permission: 'messages' },
    { id: 'consultation', label: 'Consultation', icon: Stethoscope, path: '/consultation', permission: 'consultations' },
    { id: 'billing', label: 'Facturation', icon: CreditCard, path: '/billing', permission: 'billing' },
    { id: 'administration', label: 'Administration', icon: Settings, path: '/administration', permission: 'admin' }
  ];

  const hasPermission = (permission) => {
    if (user.type === 'medecin') return true;
    if (permission === 'all') return true;
    if (permission === 'billing' || permission === 'admin') return false;
    if (permission === 'messages') return true; // Both can access messages
    return user.permissions?.includes(permission);
  };

  const filteredMenuItems = menuItems.filter(item => hasPermission(item.permission));

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar - Responsive */}
      <div className={`responsive-sidebar ${isOpen ? 'translate-x-0' : 'responsive-sidebar-hidden'}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="bg-primary-500 p-1.5 sm:p-2 rounded-lg">
              <Stethoscope className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900 text-sm sm:text-base">Cabinet</h1>
              <p className="text-xs sm:text-sm text-gray-500">Médical</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <X className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 sm:p-4 flex-1">
          <ul className="space-y-1">
            {filteredMenuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <li key={item.id}>
                  <Link
                    to={item.path}
                    onClick={onClose}
                    className={`flex items-center space-x-2 sm:space-x-3 px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 text-xs sm:text-sm ${
                      isActive 
                        ? 'bg-primary-100 text-primary-700 font-medium shadow-sm' 
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span className="hidden sm:inline lg:inline">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Info - Responsive */}
        <div className="p-3 sm:p-4 border-t border-gray-200">
          <div className="bg-gray-50 rounded-lg p-2 sm:p-3">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="bg-primary-100 p-1.5 sm:p-2 rounded-full">
                <Stethoscope className="w-3 h-3 sm:w-4 sm:h-4 text-primary-600" />
              </div>
              <div className="hidden sm:block lg:block">
                <p className="font-medium text-gray-900 text-xs sm:text-sm">{user.name}</p>
                <p className="text-xs text-gray-500 capitalize">{user.type}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;