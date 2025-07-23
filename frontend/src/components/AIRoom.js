import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Clock, 
  Users, 
  AlertTriangle, 
  TrendingUp, 
  MessageCircle,
  Phone,
  Calendar,
  Target,
  Activity,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Zap,
  Eye,
  PhoneCall
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AIRoom = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [aiData, setAiData] = useState({
    queue: [],
    predictions: {},
    doctorAnalytics: {},
    patientClassification: {},
    queueOptimization: {},
    realTimeMetrics: {}
  });
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [aiSettings, setAiSettings] = useState({
    autoOptimization: true,
    whatsappNotifications: true,
    predictiveRescheduling: true,
    emergencyMode: false
  });
  const [wsConnection, setWsConnection] = useState(null);
  const intervalRef = useRef(null);

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Initialize AI Room data and WebSocket connection
  useEffect(() => {
    initializeAIRoom();
    initializeWebSocket();
    
    // Set up real-time updates every 10 seconds
    intervalRef.current = setInterval(() => {
      fetchAIData();
    }, 10000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [selectedDate]);

  const initializeAIRoom = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/ai-room/initialize`);
      await fetchAIData();
    } catch (error) {
      console.error('Error initializing AI Room:', error);
      toast.error('Erreur lors de l\'initialisation de l\'AI Room');
    } finally {
      setLoading(false);
    }
  };

  const fetchAIData = async () => {
    try {
      const [queueResponse, predictionsResponse, analyticsResponse, metricsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/ai-room/queue?date=${selectedDate}`),
        axios.get(`${API_BASE_URL}/api/ai-room/predictions?date=${selectedDate}`),
        axios.get(`${API_BASE_URL}/api/ai-room/doctor-analytics`),
        axios.get(`${API_BASE_URL}/api/ai-room/metrics?date=${selectedDate}`)
      ]);

      setAiData({
        queue: queueResponse.data.queue || [],
        predictions: predictionsResponse.data || {},
        doctorAnalytics: analyticsResponse.data || {},
        patientClassification: predictionsResponse.data.patientClassification || {},
        queueOptimization: predictionsResponse.data.queueOptimization || {},
        realTimeMetrics: metricsResponse.data || {}
      });
    } catch (error) {
      console.error('Error fetching AI data:', error);
    }
  };

  const initializeWebSocket = () => {
    try {
      let wsUrl;
      if (API_BASE_URL.startsWith('http://') || API_BASE_URL.startsWith('https://')) {
        const backendUrl = new URL(API_BASE_URL);
        const wsProtocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${wsProtocol}//${backendUrl.host}/api/ai-room/ws`;
      } else {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${wsProtocol}//${host}/api/ai-room/ws`;
      }
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('AI Room WebSocket connected');
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onerror = (error) => {
        console.error('AI Room WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('AI Room WebSocket disconnected');
        setWsConnection(null);
      };
    } catch (error) {
      console.error('Failed to initialize AI Room WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'queue_update':
        setAiData(prev => ({ ...prev, queue: data.queue }));
        break;
      case 'prediction_update':
        setAiData(prev => ({ ...prev, predictions: data.predictions }));
        break;
      case 'notification':
        toast.success(data.message);
        break;
      case 'alert':
        toast.error(data.message);
        break;
      default:
        break;
    }
  };

  const optimizeQueue = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/ai-room/optimize-queue`, {
        date: selectedDate,
        settings: aiSettings
      });
      toast.success('File d\'attente optimisée avec succès');
      await fetchAIData();
    } catch (error) {
      console.error('Error optimizing queue:', error);
      toast.error('Erreur lors de l\'optimisation de la file');
    }
  };

  const sendWhatsAppUpdate = async (patientId, message) => {
    try {
      await axios.post(`${API_BASE_URL}/api/ai-room/send-whatsapp`, {
        patient_id: patientId,
        message: message
      });
      toast.success('Message WhatsApp envoyé');
    } catch (error) {
      console.error('Error sending WhatsApp:', error);
      toast.error('Erreur lors de l\'envoi WhatsApp');
    }
  };

  const getWaitingTimeColor = (waitTime) => {
    if (waitTime <= 15) return 'text-green-600 bg-green-100';
    if (waitTime <= 30) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'high': return <TrendingUp className="w-4 h-4 text-orange-500" />;
      case 'normal': return <Clock className="w-4 h-4 text-blue-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const QueueCard = ({ patient, index }) => (
    <div className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-600 font-semibold text-sm">{index + 1}</span>
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">
              {patient.patient_prenom} {patient.patient_nom}
            </h4>
            <p className="text-sm text-gray-600">{patient.heure} - {patient.type_rdv}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getPriorityIcon(patient.ai_priority)}
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getWaitingTimeColor(patient.predicted_wait_time)}`}>
            {patient.predicted_wait_time}min
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Arrivée prévue:</span>
          <p className="font-medium">{patient.suggested_arrival_time}</p>
        </div>
        <div>
          <span className="text-gray-500">Complexité:</span>
          <p className="font-medium">{patient.complexity_score}/10</p>
        </div>
        <div>
          <span className="text-gray-500">Ponctualité:</span>
          <p className="font-medium">{patient.punctuality_score}%</p>
        </div>
        <div>
          <span className="text-gray-500">Durée prévue:</span>
          <p className="font-medium">{patient.predicted_duration}min</p>
        </div>
      </div>

      <div className="flex justify-between items-center mt-4 pt-3 border-t">
        <div className="flex space-x-2">
          <button
            onClick={() => sendWhatsAppUpdate(patient.patient_id, `Votre RDV dans 1h. Arrivez à ${patient.suggested_arrival_time} pour éviter l'attente.`)}
            className="text-green-600 hover:text-green-700 p-1"
            title="Envoyer rappel WhatsApp"
          >
            <PhoneCall className="w-4 h-4" />
          </button>
          <button
            className="text-blue-600 hover:text-blue-700 p-1"
            title="Voir détails patient"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          patient.status === 'arrived' ? 'bg-green-100 text-green-700' :
          patient.status === 'waiting' ? 'bg-yellow-100 text-yellow-700' :
          patient.status === 'in_consultation' ? 'bg-blue-100 text-blue-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {patient.status_label}
        </span>
      </div>
    </div>
  );

  const MetricCard = ({ icon: Icon, title, value, subtitle, color, trend }) => (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
            <Icon className={`w-5 h-5 ${color}`} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
            <p className={`text-lg font-bold ${color}`}>{value}</p>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
          </div>
        </div>
        {trend && (
          <div className={`flex items-center text-xs ${
            trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
          }`}>
            <TrendingUp className="w-3 h-3 mr-1" />
            {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <Brain className="w-8 h-8 text-primary-500" />
            <span>AI Room - Gestion Intelligente</span>
          </h1>
          <p className="text-gray-600">Optimisation automatique des files d'attente avec IA</p>
        </div>
        <div className="flex items-center space-x-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            onClick={optimizeQueue}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors flex items-center space-x-2"
          >
            <Zap className="w-4 h-4" />
            <span>Optimiser</span>
          </button>
        </div>
      </div>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Users}
          title="File d'attente"
          value={aiData.queue.length}
          subtitle="Patients en attente"
          color="text-blue-600"
          trend={aiData.realTimeMetrics.queue_trend}
        />
        <MetricCard
          icon={Clock}
          title="Temps moyen"
          value={`${aiData.realTimeMetrics.avg_wait_time || 0}min`}
          subtitle="Attente prédite"
          color="text-yellow-600"
          trend={aiData.realTimeMetrics.wait_trend}
        />
        <MetricCard
          icon={Activity}
          title="Efficacité IA"
          value={`${aiData.doctorAnalytics.efficiency_score || 85}%`}
          subtitle="Score d'optimisation"
          color="text-green-600"
          trend={aiData.realTimeMetrics.efficiency_trend}
        />
        <MetricCard
          icon={Target}
          title="Prédictions"
          value={`${aiData.predictions.accuracy || 92}%`}
          subtitle="Précision des prédictions"
          color="text-purple-600"
          trend={aiData.realTimeMetrics.prediction_trend}
        />
      </div>

      {/* AI Settings & Controls */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Settings className="w-5 h-5" />
          <span>Paramètres IA</span>
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={aiSettings.autoOptimization}
              onChange={(e) => setAiSettings(prev => ({ ...prev, autoOptimization: e.target.checked }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Optimisation auto</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={aiSettings.whatsappNotifications}
              onChange={(e) => setAiSettings(prev => ({ ...prev, whatsappNotifications: e.target.checked }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Notifications WhatsApp</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={aiSettings.predictiveRescheduling}
              onChange={(e) => setAiSettings(prev => ({ ...prev, predictiveRescheduling: e.target.checked }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Reprog. prédictive</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={aiSettings.emergencyMode}
              onChange={(e) => setAiSettings(prev => ({ ...prev, emergencyMode: e.target.checked }))}
              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <span className="text-sm text-red-700">Mode urgence</span>
          </label>
        </div>
      </div>

      {/* Doctor Analytics & Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analyse du Médecin</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Efficacité matinale</span>
              <span className="font-medium">{aiData.doctorAnalytics.morning_efficiency || 92}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Durée moyenne consultation</span>
              <span className="font-medium">{aiData.doctorAnalytics.avg_consultation_duration || 18}min</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Ponctualité</span>
              <span className="font-medium">{aiData.doctorAnalytics.punctuality_score || 87}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Prochaine pause suggérée</span>
              <span className="font-medium">{aiData.predictions.next_break || '11:30'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Prédictions IA</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Retard prévu fin journée</span>
              <span className="font-medium text-orange-600">{aiData.predictions.end_day_delay || 12}min</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Patients à risque d'absence</span>
              <span className="font-medium text-red-600">{aiData.predictions.no_show_risk || 2}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Créneaux optimaux libres</span>
              <span className="font-medium text-green-600">{aiData.predictions.optimal_slots || 3}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Score satisfaction prédite</span>
              <span className="font-medium">{aiData.predictions.satisfaction_score || 94}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI-Optimized Patient Queue */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <RefreshCw className="w-5 h-5" />
            <span>File d'Attente Optimisée par IA</span>
          </h3>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-100 rounded-full"></div>
              <span>≤15min</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-yellow-100 rounded-full"></div>
              <span>15-30min</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-100 rounded-full"></div>
              <span>>30min</span>
            </div>
          </div>
        </div>

        {aiData.queue.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {aiData.queue.map((patient, index) => (
              <QueueCard key={patient.appointment_id} patient={patient} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Brain className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <p className="text-gray-500">Aucun patient dans la file d'attente</p>
            <p className="text-sm text-gray-400">L'IA optimisera automatiquement les prochains rendez-vous</p>
          </div>
        )}
      </div>

      {/* AI Insights & Recommendations */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border border-primary-200 p-4">
        <h3 className="text-lg font-semibold text-primary-900 mb-3 flex items-center space-x-2">
          <Brain className="w-5 h-5" />
          <span>Recommandations IA</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white bg-opacity-60 rounded-lg p-3">
            <h4 className="font-medium text-primary-800 mb-2">🎯 Optimisation Immédiate</h4>
            <p className="text-sm text-primary-700">
              Décaler Mme Martin de 15min permettrait d'économiser 8min d'attente globale
            </p>
          </div>
          <div className="bg-white bg-opacity-60 rounded-lg p-3">
            <h4 className="font-medium text-primary-800 mb-2">📱 Communication Proactive</h4>
            <p className="text-sm text-primary-700">
              3 patients bénéficieraient d'un message WhatsApp pour optimiser leur arrivée
            </p>
          </div>
          <div className="bg-white bg-opacity-60 rounded-lg p-3">
            <h4 className="font-medium text-primary-800 mb-2">⚡ Performance</h4>
            <p className="text-sm text-primary-700">
              Votre efficacité est 15% supérieure les mardis matins - concentrer les cas complexes
            </p>
          </div>
          <div className="bg-white bg-opacity-60 rounded-lg p-3">
            <h4 className="font-medium text-primary-800 mb-2">🔮 Prédiction</h4>
            <p className="text-sm text-primary-700">
              85% de chance que M. Dubois arrive en retard - ajuster automatiquement
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIRoom;