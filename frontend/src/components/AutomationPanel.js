import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Activity, 
  Clock, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Calendar,
  Users,
  BarChart3,
  Zap,
  PlayCircle,
  PauseCircle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AutomationPanel = () => {
  const [automationStatus, setAutomationStatus] = useState(null);
  const [automationSettings, setAutomationSettings] = useState(null);
  const [scheduleOptimizations, setScheduleOptimizations] = useState(null);
  const [proactiveRecommendations, setProactiveRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchAutomationData();
    
    // Refresh automation data every 30 seconds
    const interval = setInterval(fetchAutomationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAutomationData = async () => {
    try {
      setLoading(true);
      const today = new Date().toISOString().split('T')[0];
      
      // Fetch automation status, settings, optimizations, and recommendations in parallel
      const [statusRes, settingsRes, optimizationsRes, recommendationsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/automation/status`),
        axios.get(`${API_BASE_URL}/api/automation/settings`),
        axios.get(`${API_BASE_URL}/api/automation/schedule-optimization?date=${today}`),
        axios.get(`${API_BASE_URL}/api/automation/proactive-recommendations`)
      ]);
      
      setAutomationStatus(statusRes.data);
      setAutomationSettings(settingsRes.data);
      setScheduleOptimizations(optimizationsRes.data);
      setProactiveRecommendations(recommendationsRes.data);
      
    } catch (error) {
      console.error('Error fetching automation data:', error);
      toast.error('Erreur lors du chargement des données d\'automation');
    } finally {
      setLoading(false);
    }
  };

  const updateAutomationSettings = async (newSettings) => {
    try {
      await axios.put(`${API_BASE_URL}/api/automation/settings`, newSettings);
      setAutomationSettings(newSettings);
      toast.success('Paramètres d\'automation mis à jour');
      fetchAutomationData(); // Refresh status after settings change
    } catch (error) {
      console.error('Error updating automation settings:', error);
      toast.error('Erreur lors de la mise à jour des paramètres');
    }
  };

  const applyOptimization = async (optimization) => {
    try {
      await axios.post(`${API_BASE_URL}/api/automation/apply-optimization`, optimization);
      toast.success(`Optimisation appliquée - ${optimization.potential_time_saved}min économisées`);
      fetchAutomationData(); // Refresh data after applying optimization
    } catch (error) {
      console.error('Error applying optimization:', error);
      toast.error('Erreur lors de l\'application de l\'optimisation');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Zap className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Automation Intelligente</h3>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header with Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Automation Intelligente</h3>
          </div>
          <div className="flex items-center space-x-2">
            {automationStatus?.automation_active ? (
              <>
                <PlayCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600 font-medium">Active</span>
              </>
            ) : (
              <>
                <PauseCircle className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-500 font-medium">Pause</span>
              </>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Paramètres"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={fetchAutomationData}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Actualiser"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && automationSettings && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-gray-900 mb-3">Paramètres d'Automation</h4>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries({
              auto_schedule_optimization: 'Optimisation automatique des horaires',
              auto_conflict_resolution: 'Résolution automatique des conflits',
              auto_reschedule_suggestions: 'Suggestions de reprogrammation',
              proactive_workflow_alerts: 'Alertes workflow proactives'
            }).map(([key, label]) => (
              <label key={key} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={automationSettings[key]}
                  onChange={(e) => {
                    const newSettings = { ...automationSettings, [key]: e.target.checked };
                    updateAutomationSettings(newSettings);
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Status Metrics */}
      {automationStatus && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-600">Optimisations</span>
            </div>
            <div className="mt-1">
              <span className="text-2xl font-bold text-blue-900">
                {automationStatus.metrics.optimizations_available}
              </span>
              <span className="text-sm text-blue-600 ml-1">disponibles</span>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-600">Temps économisé</span>
            </div>
            <div className="mt-1">
              <span className="text-2xl font-bold text-green-900">
                {automationStatus.metrics.time_saved_today_minutes}
              </span>
              <span className="text-sm text-green-600 ml-1">min</span>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-600">Priorité haute</span>
            </div>
            <div className="mt-1">
              <span className="text-2xl font-bold text-yellow-900">
                {automationStatus.metrics.high_priority_items}
              </span>
              <span className="text-sm text-yellow-600 ml-1">éléments</span>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-600">Appliquées</span>
            </div>
            <div className="mt-1">
              <span className="text-2xl font-bold text-purple-900">
                {automationStatus.metrics.optimizations_applied_today}
              </span>
              <span className="text-sm text-purple-600 ml-1">aujourd'hui</span>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Optimizations */}
      {scheduleOptimizations && scheduleOptimizations.optimizations.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <Calendar className="w-4 h-4 text-blue-600" />
            <h4 className="font-medium text-gray-900">Optimisations d'Horaires</h4>
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
              {scheduleOptimizations.optimizations.length}
            </span>
          </div>
          <div className="space-y-3">
            {scheduleOptimizations.optimizations.slice(0, 3).map((optimization, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      optimization.optimization_type === 'conflict_resolution' 
                        ? 'bg-red-100 text-red-800'
                        : optimization.optimization_type === 'wait_time_reduction'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {optimization.optimization_type.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-600">
                      {optimization.current_time} → {optimization.suggested_time}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-green-600">
                      +{optimization.potential_time_saved}min
                    </span>
                    <button
                      onClick={() => applyOptimization(optimization)}
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                    >
                      Appliquer
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{optimization.reason}</p>
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">Confiance:</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${optimization.confidence_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">
                      {(optimization.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Proactive Recommendations */}
      {proactiveRecommendations && proactiveRecommendations.recommendations.length > 0 && (
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <h4 className="font-medium text-gray-900">Recommandations Proactives</h4>
            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
              {proactiveRecommendations.recommendations.length}
            </span>
          </div>
          <div className="space-y-3">
            {proactiveRecommendations.recommendations.slice(0, 3).map((recommendation, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-gray-900">{recommendation.title}</h5>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      recommendation.impact === 'high' 
                        ? 'bg-red-100 text-red-800'
                        : recommendation.impact === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {recommendation.impact}
                    </span>
                    <span className="text-sm text-green-600 font-medium">
                      +{recommendation.estimated_time_saved}min
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{recommendation.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    Difficulté: {recommendation.implementation_difficulty}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">Confiance:</span>
                    <span className="text-xs text-gray-600">
                      {(recommendation.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!scheduleOptimizations?.optimizations?.length && !proactiveRecommendations?.recommendations?.length) && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">Tout va bien !</h4>
          <p className="text-gray-600">
            Aucune optimisation nécessaire pour le moment. 
            L'automation surveille en continu votre planning.
          </p>
        </div>
      )}
    </div>
  );
};

export default AutomationPanel;