import React, { useState, useEffect } from 'react';
import { 
  MessageCircle, 
  Send, 
  Clock, 
  Users, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Edit3,
  Copy,
  Phone,
  Calendar,
  Timer,
  User,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const WhatsAppHub = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [waitingQueue, setWaitingQueue] = useState([]);
  const [messageTemplates, setMessageTemplates] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customMessage, setCustomMessage] = useState('');
  const [messageHistory, setMessageHistory] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchInitialData();
    // Auto-refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchWaitingQueue, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchPatients(),
        fetchWaitingQueue(),
        fetchMessageTemplates(),
        fetchMessageHistory()
      ]);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(response.data.patients || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const fetchWaitingQueue = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API_BASE_URL}/api/whatsapp-hub/queue?date=${today}`);
      setWaitingQueue(response.data.queue || []);
    } catch (error) {
      console.error('Error fetching waiting queue:', error);
    }
  };

  const fetchMessageTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/whatsapp-hub/templates`);
      setMessageTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error fetching message templates:', error);
    }
  };

  const fetchMessageHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/whatsapp-hub/history`);
      setMessageHistory(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching message history:', error);
    }
  };

  const sendWhatsAppMessage = async (patientId, message, templateId = null) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/whatsapp-hub/send`, {
        patient_id: patientId,
        message: message,
        template_id: templateId,
        sent_by: user.full_name
      });

      toast.success('Message WhatsApp envoyé avec succès');
      
      // Refresh message history
      await fetchMessageHistory();
      
      // Clear form
      setSelectedPatient(null);
      setSelectedTemplate(null);
      setCustomMessage('');
      
      return response.data;
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
      toast.error('Erreur lors de l\'envoi du message');
    }
  };

  const generateContextualMessage = (template, patient, queueInfo = null) => {
    let message = template.content;
    
    // Replace patient variables
    message = message.replace('{patient_name}', patient.prenom);
    message = message.replace('{patient_full_name}', `${patient.prenom} ${patient.nom}`);
    
    // Replace queue variables if available
    if (queueInfo) {
      message = message.replace('{queue_position}', queueInfo.position);
      message = message.replace('{estimated_wait}', queueInfo.estimated_wait);
      message = message.replace('{appointment_time}', queueInfo.appointment_time);
    }
    
    // Replace time variables
    const now = new Date();
    message = message.replace('{current_time}', now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }));
    message = message.replace('{current_date}', now.toLocaleDateString('fr-FR'));
    
    return message;
  };

  const getPatientQueueInfo = (patientId) => {
    const queueItem = waitingQueue.find(item => item.patient_id === patientId);
    if (queueItem) {
      return {
        position: queueItem.queue_position,
        estimated_wait: queueItem.estimated_wait_time,
        appointment_time: queueItem.appointment_time,
        status: queueItem.status
      };
    }
    return null;
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    if (selectedPatient) {
      const queueInfo = getPatientQueueInfo(selectedPatient.id);
      const generatedMessage = generateContextualMessage(template, selectedPatient, queueInfo);
      setCustomMessage(generatedMessage);
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    if (selectedTemplate) {
      const queueInfo = getPatientQueueInfo(patient.id);
      const generatedMessage = generateContextualMessage(selectedTemplate, patient, queueInfo);
      setCustomMessage(generatedMessage);
    }
  };

  const filteredPatients = patients.filter(patient => {
    const matchesSearch = patient.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         patient.prenom.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterStatus === 'all') return matchesSearch;
    if (filterStatus === 'waiting') {
      const inQueue = waitingQueue.some(item => item.patient_id === patient.id);
      return matchesSearch && inQueue;
    }
    if (filterStatus === 'today') {
      const today = new Date().toISOString().split('T')[0];
      // This would need to be implemented based on appointments
      return matchesSearch;
    }
    
    return matchesSearch;
  });

  const TemplateCard = ({ template }) => (
    <div 
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        selectedTemplate?.id === template.id 
          ? 'border-primary-500 bg-primary-50' 
          : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={() => handleTemplateSelect(template)}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-gray-900">{template.name}</h4>
        <span className={`px-2 py-1 text-xs rounded-full ${
          template.category === 'confirmation' ? 'bg-green-100 text-green-700' :
          template.category === 'delay' ? 'bg-yellow-100 text-yellow-700' :
          template.category === 'position' ? 'bg-blue-100 text-blue-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {template.category}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-2">{template.description}</p>
      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
        {template.preview}
      </div>
    </div>
  );

  const PatientCard = ({ patient }) => {
    const queueInfo = getPatientQueueInfo(patient.id);
    
    return (
      <div 
        className={`p-3 border rounded-lg cursor-pointer transition-all ${
          selectedPatient?.id === patient.id 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-200 hover:border-gray-300'
        }`}
        onClick={() => handlePatientSelect(patient)}
      >
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">
              {patient.prenom} {patient.nom}
            </h4>
            <p className="text-sm text-gray-600">{patient.numero_whatsapp}</p>
          </div>
          <div className="text-right">
            {queueInfo && (
              <div className="text-xs text-blue-600">
                Position: {queueInfo.position}
                <br />
                Attente: {queueInfo.estimated_wait}min
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const MessageHistoryItem = ({ message }) => (
    <div className="p-3 border-l-4 border-primary-200 bg-gray-50 rounded-r-lg mb-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4 text-gray-600" />
          <span className="font-medium text-gray-900">{message.patient_name}</span>
          <span className="text-xs text-gray-500">{message.sent_by}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">
            {new Date(message.sent_at).toLocaleString('fr-FR')}
          </span>
          <span className={`w-2 h-2 rounded-full ${
            message.status === 'sent' ? 'bg-green-500' :
            message.status === 'delivered' ? 'bg-blue-500' :
            message.status === 'read' ? 'bg-purple-500' :
            'bg-gray-400'
          }`} />
        </div>
      </div>
      <p className="text-sm text-gray-700">{message.content}</p>
      {message.template_used && (
        <p className="text-xs text-gray-500 mt-1">Template: {message.template_used}</p>
      )}
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
            <MessageCircle className="w-8 h-8 text-green-500" />
            <span>Hub WhatsApp</span>
          </h1>
          <p className="text-gray-600">Gestion des messages patients avec templates intelligents</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchWaitingQueue}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Actualiser</span>
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center space-x-3">
            <Users className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-gray-600">File d'attente</p>
              <p className="text-2xl font-bold text-blue-600">{waitingQueue.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center space-x-3">
            <MessageCircle className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-sm font-medium text-gray-600">Messages aujourd'hui</p>
              <p className="text-2xl font-bold text-green-600">
                {messageHistory.filter(m => 
                  new Date(m.sent_at).toDateString() === new Date().toDateString()
                ).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center space-x-3">
            <Clock className="w-8 h-8 text-yellow-500" />
            <div>
              <p className="text-sm font-medium text-gray-600">Temps d'attente moyen</p>
              <p className="text-2xl font-bold text-yellow-600">
                {waitingQueue.length > 0 
                  ? Math.round(waitingQueue.reduce((sum, item) => sum + item.estimated_wait_time, 0) / waitingQueue.length)
                  : 0}min
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-8 h-8 text-purple-500" />
            <div>
              <p className="text-sm font-medium text-gray-600">Templates disponibles</p>
              <p className="text-2xl font-bold text-purple-600">{messageTemplates.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Message Templates */}
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Templates de Messages</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {messageTemplates.map((template) => (
              <TemplateCard key={template.id} template={template} />
            ))}
          </div>
        </div>

        {/* Patient Selection */}
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Sélection Patient</h3>
            <div className="flex items-center space-x-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">Tous</option>
                <option value="waiting">En attente</option>
                <option value="today">Aujourd'hui</option>
              </select>
            </div>
          </div>
          
          <div className="mb-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher un patient..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {filteredPatients.map((patient) => (
              <PatientCard key={patient.id} patient={patient} />
            ))}
          </div>
        </div>

        {/* Message Composer */}
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Composer Message</h3>
          
          {selectedPatient && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-blue-900">
                  {selectedPatient.prenom} {selectedPatient.nom}
                </span>
              </div>
              <p className="text-sm text-blue-700">{selectedPatient.numero_whatsapp}</p>
              {getPatientQueueInfo(selectedPatient.id) && (
                <div className="mt-2 text-xs text-blue-600">
                  Position: {getPatientQueueInfo(selectedPatient.id).position} | 
                  Attente: {getPatientQueueInfo(selectedPatient.id).estimated_wait}min
                </div>
              )}
            </div>
          )}
          
          {selectedTemplate && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-4 h-4 text-green-600" />
                <span className="font-medium text-green-900">{selectedTemplate.name}</span>
              </div>
              <p className="text-sm text-green-700">{selectedTemplate.description}</p>
            </div>
          )}
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message WhatsApp
            </label>
            <textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              rows={6}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Tapez votre message ici ou sélectionnez un template..."
            />
            <div className="text-xs text-gray-500 mt-1">
              {customMessage.length} caractères
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => {
                if (selectedPatient && customMessage.trim()) {
                  sendWhatsAppMessage(
                    selectedPatient.id, 
                    customMessage.trim(), 
                    selectedTemplate?.id
                  );
                } else {
                  toast.error('Veuillez sélectionner un patient et saisir un message');
                }
              }}
              disabled={!selectedPatient || !customMessage.trim()}
              className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Envoyer WhatsApp</span>
            </button>
            
            <button
              onClick={() => {
                setSelectedPatient(null);
                setSelectedTemplate(null);
                setCustomMessage('');
              }}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Message History */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Historique des Messages</h3>
        <div className="max-h-96 overflow-y-auto space-y-3">
          {messageHistory.slice(0, 20).map((message) => (
            <MessageHistoryItem key={message.id} message={message} />
          ))}
          {messageHistory.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Aucun message envoyé aujourd'hui</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WhatsAppHub;