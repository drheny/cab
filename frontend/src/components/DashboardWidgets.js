import React, { useState, useEffect } from 'react';
import { 
  Eye, 
  EyeOff, 
  Settings, 
  RefreshCw, 
  Maximize2, 
  Minimize2,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  Clock,
  Users,
  Zap
} from 'lucide-react';

const DashboardWidget = ({ 
  title, 
  icon: Icon, 
  children, 
  refreshable = false, 
  onRefresh,
  expandable = false,
  initialExpanded = false,
  colorScheme = 'blue',
  className = '',
  loading = false
}) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [isVisible, setIsVisible] = useState(true);

  const colorClasses = {
    blue: 'border-blue-200 bg-blue-50',
    green: 'border-green-200 bg-green-50',
    purple: 'border-purple-200 bg-purple-50',
    yellow: 'border-yellow-200 bg-yellow-50',
    red: 'border-red-200 bg-red-50',
    gray: 'border-gray-200 bg-gray-50'
  };

  const iconColorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    purple: 'text-purple-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    gray: 'text-gray-600'
  };

  if (!isVisible) {
    return (
      <div className="bg-gray-100 rounded-lg p-4 border-2 border-dashed border-gray-300">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">{title} (masqué)</span>
          <button
            onClick={() => setIsVisible(true)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Afficher le widget"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border transition-all duration-300 ${
      isExpanded ? 'col-span-full' : ''
    } ${className}`}>
      {/* Header */}
      <div className={`px-4 py-3 border-b border-gray-100 ${colorClasses[colorScheme]} rounded-t-lg`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon className={`w-5 h-5 ${iconColorClasses[colorScheme]}`} />
            <h3 className="font-semibold text-gray-900">{title}</h3>
          </div>
          
          <div className="flex items-center space-x-1">
            {refreshable && (
              <button
                onClick={onRefresh}
                disabled={loading}
                className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-white/50"
                title="Actualiser"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            )}
            
            {expandable && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-white/50"
                title={isExpanded ? "Réduire" : "Agrandir"}
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}
            
            <button
              onClick={() => setIsVisible(false)}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-white/50"
              title="Masquer le widget"
            >
              <EyeOff className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className={`p-4 ${isExpanded ? 'min-h-96' : ''}`}>
        {loading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
};

const MetricCard = ({ title, value, unit, trend, trendValue, icon: Icon, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    red: 'bg-red-50 text-red-600 border-red-200'
  };

  const trendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Activity;
  const trendColorClass = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600';

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className="w-4 h-4" />
          <span className="text-sm font-medium">{title}</span>
        </div>
        {trend && (
          <div className="flex items-center space-x-1">
            {React.createElement(trendIcon, { className: `w-3 h-3 ${trendColorClass}` })}
            <span className={`text-xs ${trendColorClass}`}>
              {trendValue}
            </span>
          </div>
        )}
      </div>
      <div className="flex items-baseline space-x-1">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-600">{unit}</span>}
      </div>
    </div>
  );
};

const QuickActionButton = ({ title, description, icon: Icon, onClick, color = 'blue', disabled = false }) => {
  const colorClasses = {
    blue: 'bg-blue-600 hover:bg-blue-700 text-white',
    green: 'bg-green-600 hover:bg-green-700 text-white',
    purple: 'bg-purple-600 hover:bg-purple-700 text-white',
    yellow: 'bg-yellow-600 hover:bg-yellow-700 text-white',
    red: 'bg-red-600 hover:bg-red-700 text-white'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full p-4 rounded-lg transition-colors ${
        disabled ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : colorClasses[color]
      }`}
    >
      <div className="flex items-center space-x-3">
        <Icon className="w-5 h-5" />
        <div className="text-left">
          <div className="font-medium">{title}</div>
          <div className="text-sm opacity-90">{description}</div>
        </div>
      </div>
    </button>
  );
};

const ProgressBar = ({ label, value, maxValue, color = 'blue', showPercentage = true }) => {
  const percentage = Math.min((value / maxValue) * 100, 100);
  
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showPercentage && (
          <span className="text-sm text-gray-600">{percentage.toFixed(0)}%</span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{value}</span>
        <span>{maxValue}</span>
      </div>
    </div>
  );
};

const AlertBadge = ({ type = 'info', children }) => {
  const typeClasses = {
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    error: 'bg-red-100 text-red-800 border-red-200'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${typeClasses[type]}`}>
      {children}
    </span>
  );
};

const StatGrid = ({ stats, columns = 4 }) => {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-${columns} gap-4`}>
      {stats.map((stat, index) => (
        <MetricCard key={index} {...stat} />
      ))}
    </div>
  );
};

// Export all components
export {
  DashboardWidget,
  MetricCard,
  QuickActionButton,
  ProgressBar,
  AlertBadge,
  StatGrid
};