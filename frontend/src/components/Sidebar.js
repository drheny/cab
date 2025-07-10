import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Users, 
  Calendar, 
  Clock, 
  Stethoscope, 
  CreditCard, 
  Settings,
  X 
} from 'lucide-react';

const Sidebar = ({ user, isOpen, onClose }) => {
  const location = useLocation();

  const menuItems = [
    { id: 'dashboard', label: 'Tableau de bord', icon: Home, path: '/dashboard', permission: 'all' },
    { id: 'patients', label: 'Patients', icon: Users, path: '/patients', permission: 'patients' },
    { id: 'calendar', label: 'Calendrier', icon: Calendar, path: '/calendar', permission: 'appointments' },
    { id: 'waiting-room', label: 'Salles d\'attente', icon: Clock, path: '/waiting-room', permission: 'waiting_room' },
    { id: 'consultation', label: 'Consultation', icon: Stethoscope, path: '/consultation', permission: 'consultations' },
    { id: 'billing', label: 'Facturation', icon: CreditCard, path: '/billing', permission: 'billing' },
    { id: 'administration', label: 'Administration', icon: Settings, path: '/administration', permission: 'admin' }
  ];

  const hasPermission = (permission) => {
    if (user.type === 'medecin') return true;
    if (permission === 'all') return true;
    if (permission === 'billing' || permission === 'admin') return false;
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
      
      {/* Sidebar - Fixed for PC */}
      <div className="pc-sidebar-fixed">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-500 p-2 rounded-lg">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900">Cabinet</h1>
              <p className="text-sm text-gray-500">Médical</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 flex-1">
          <ul className="space-y-1">
            {filteredMenuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <li key={item.id}>
                  <Link
                    to={item.path}
                    onClick={onClose}
                    className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm ${
                      isActive 
                        ? 'bg-primary-100 text-primary-700 font-medium shadow-sm' 
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Info - Compact for PC */}
        <div className="p-4 border-t border-gray-200">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-100 p-2 rounded-full">
                <Stethoscope className="w-4 h-4 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">{user.name}</p>
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