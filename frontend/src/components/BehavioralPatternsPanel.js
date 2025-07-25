import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Clock, 
  MessageCircle, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Eye,
  RefreshCw,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const BehavioralPatternsPanel = () => {
  const [behavioralData, setBehavioralData] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('overview'); // 'overview', 'punctuality', 'communication', 'satisfaction'
  
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchBehavioralData();
  }, []);

  const fetchBehavioralData = async () => {
    try {
      setLoading(true);
      
      // Get demo patients and their behavioral profiles
      const patientsRes = await axios.get(`${API_BASE_URL}/api/patients`);
      const patients = patientsRes.data;
      
      // Fetch behavioral profiles for each patient
      const behavioralProfiles = await Promise.all(
        patients.slice(0, 10).map(async (patient) => {
          try {
            const profileRes = await axios.get(`${API_BASE_URL}/api/ai-learning/patient-behavioral-profile?patient_id=${patient.id}`);
            return {
              patient,
              profile: profileRes.data.behavioral_profile
            };
          } catch (error) {
            console.error(`Error fetching profile for patient ${patient.id}:`, error);
            return {
              patient,
              profile: null
            };
          }
        })
      );
      
      setBehavioralData(behavioralProfiles.filter(item => item.profile));
      
    } catch (error) {
      console.error('Error fetching behavioral data:', error);
      toast.error('Erreur lors du chargement des données comportementales');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      case 'stable':
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600 bg-green-50';
    if (score >= 6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getScoreBarColor = (score) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const calculateOverviewStats = () => {
    if (!behavioralData || behavioralData.length === 0) return null;
    
    const totalPatients = behavioralData.length;
    const avgPunctuality = behavioralData.reduce((sum, item) => sum + item.profile.punctuality_score, 0) / totalPatients;
    const avgCommunication = behavioralData.reduce((sum, item) => sum + item.profile.communication_effectiveness, 0) / totalPatients;
    const avgSatisfaction = behavioralData.reduce((sum, item) => sum + item.profile.satisfaction_score, 0) / totalPatients;
    
    const reliablePatients = behavioralData.filter(item => item.profile.reliability_score >= 0.8).length;
    const atRiskPatients = behavioralData.filter(item => 
      item.profile.risk_factors && item.profile.risk_factors.length > 0
    ).length;
    
    return {
      totalPatients,
      avgPunctuality: avgPunctuality.toFixed(1),
      avgCommunication: avgCommunication.toFixed(1),
      avgSatisfaction: avgSatisfaction.toFixed(1),
      reliablePatients,
      atRiskPatients
    };
  };

  const renderOverview = () => {
    const stats = calculateOverviewStats();
    if (!stats) return null;

    return (
      <div className="space-y-6">
        {/* Overview Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Users className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-600">Patients analysés</span>
            </div>
            <span className="text-2xl font-bold text-blue-900">{stats.totalPatients}</span>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-600">Ponctualité moy.</span>
            </div>
            <span className="text-2xl font-bold text-green-900">{stats.avgPunctuality}/10</span>
          </div>

          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <MessageCircle className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-600">Communication</span>
            </div>
            <span className="text-2xl font-bold text-purple-900">{stats.avgCommunication}/10</span>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="w-4 h-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-600">Satisfaction</span>
            </div>
            <span className="text-2xl font-bold text-yellow-900">{stats.avgSatisfaction}/10</span>
          </div>

          <div className="bg-emerald-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Users className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-600">Fiables</span>
            </div>
            <span className="text-2xl font-bold text-emerald-900">{stats.reliablePatients}</span>
          </div>

          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Users className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium text-red-600">À risque</span>
            </div>
            <span className="text-2xl font-bold text-red-900">{stats.atRiskPatients}</span>
          </div>
        </div>

        {/* Top and Bottom Performers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Best Performers */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span>Meilleurs Patients</span>
            </h4>
            <div className="space-y-2">
              {behavioralData
                .sort((a, b) => b.profile.reliability_score - a.profile.reliability_score)
                .slice(0, 3)
                .map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-green-50 rounded">
                    <span className="text-sm font-medium text-gray-900">
                      {item.patient.prenom} {item.patient.nom}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${item.profile.reliability_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">
                        {(item.profile.reliability_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Patients Needing Attention */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-red-600" />
              <span>Patients à Surveiller</span>
            </h4>
            <div className="space-y-2">
              {behavioralData
                .filter(item => item.profile.risk_factors && item.profile.risk_factors.length > 0)
                .slice(0, 3)
                .map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-red-50 rounded">
                    <span className="text-sm font-medium text-gray-900">
                      {item.patient.prenom} {item.patient.nom}
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {item.profile.risk_factors.slice(0, 2).map((risk, riskIndex) => (
                        <span key={riskIndex} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                          {risk.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderDetailedView = () => {
    return (
      <div className="space-y-4">
        {behavioralData.map((item, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {item.patient.prenom} {item.patient.nom}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {item.profile.consultation_count} consultations
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getTrendIcon(item.profile.behavioral_trend)}
                <button
                  onClick={() => setSelectedPatient(item)}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Voir détails"
                >
                  <Eye className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {/* Punctuality */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Ponctualité</span>
                  <span className={`text-xs px-2 py-1 rounded ${getScoreColor(item.profile.punctuality_score)}`}>
                    {item.profile.punctuality_score.toFixed(1)}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${getScoreBarColor(item.profile.punctuality_score)}`}
                    style={{ width: `${(item.profile.punctuality_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Communication */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Communication</span>
                  <span className={`text-xs px-2 py-1 rounded ${getScoreColor(item.profile.communication_effectiveness)}`}>
                    {item.profile.communication_effectiveness.toFixed(1)}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${getScoreBarColor(item.profile.communication_effectiveness)}`}
                    style={{ width: `${(item.profile.communication_effectiveness / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Satisfaction */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Satisfaction</span>
                  <span className={`text-xs px-2 py-1 rounded ${getScoreColor(item.profile.satisfaction_score)}`}>
                    {item.profile.satisfaction_score.toFixed(1)}/10
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${getScoreBarColor(item.profile.satisfaction_score)}`}
                    style={{ width: `${(item.profile.satisfaction_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Risk Factors */}
            {item.profile.risk_factors && item.profile.risk_factors.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-gray-600">Facteurs de risque:</span>
                  {item.profile.risk_factors.map((risk, riskIndex) => (
                    <span key={riskIndex} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                      {risk.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Patterns Comportementaux</h3>
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
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Patterns Comportementaux</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('overview')}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                viewMode === 'overview' 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Vue d'ensemble
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                viewMode === 'detailed' 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Détaillé
            </button>
          </div>
          
          <button
            onClick={fetchBehavioralData}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Actualiser"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      {behavioralData && behavioralData.length > 0 ? (
        viewMode === 'overview' ? renderOverview() : renderDetailedView()
      ) : (
        <div className="text-center py-8">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">Aucune donnée disponible</h4>
          <p className="text-gray-600">
            Les patterns comportementaux apparaîtront ici après avoir collecté suffisamment de données.
          </p>
        </div>
      )}

      {/* Patient Detail Modal */}
      {selectedPatient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full m-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedPatient.patient.prenom} {selectedPatient.patient.nom}
              </h3>
              <button
                onClick={() => setSelectedPatient(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-600">Score de fiabilité global</span>
                <div className="mt-1 flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-blue-500 h-3 rounded-full" 
                      style={{ width: `${selectedPatient.profile.reliability_score * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {(selectedPatient.profile.reliability_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div>
                <span className="text-sm text-gray-600">Créneaux préférés</span>
                <div className="mt-1 flex flex-wrap gap-2">
                  {selectedPatient.profile.preferred_time_slots.map((slot, index) => (
                    <span key={index} className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {slot}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-sm text-gray-600">Tendance comportementale</span>
                <div className="mt-1 flex items-center space-x-2">
                  {getTrendIcon(selectedPatient.profile.behavioral_trend)}
                  <span className="text-sm text-gray-900 capitalize">
                    {selectedPatient.profile.behavioral_trend}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BehavioralPatternsPanel;