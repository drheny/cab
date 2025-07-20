import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Calendar, 
  Clock, 
  DollarSign, 
  MessageCircle,
  Phone,
  AlertCircle,
  Gift,
  PhoneCall,
  Eye,
  X,
  MessageSquare
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Dashboard = ({ user }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_rdv: 0,
    rdv_restants: 0,
    rdv_attente: 0,
    rdv_en_cours: 0,
    rdv_termines: 0,
    recette_jour: 0,
    total_patients: 0,
    duree_attente_moyenne: 0
  });
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  
  // Data states
  const [birthdays, setBirthdays] = useState([]);
  const [phoneReminders, setPhoneReminders] = useState([]);
  
  // Messaging states
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [editingMessage, setEditingMessage] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  const handleAddPatient = () => {
    // Naviguer vers la page patients avec un paramètre pour ouvrir le modal
    navigate('/patients?action=add');
  };

  const handleNewAppointment = () => {
    // Naviguer vers la page calendrier avec un paramètre pour ouvrir le modal
    navigate('/calendar?action=add');
  };

  const handlePhoneReminders = () => {
    // Afficher une notification avec les rappels téléphoniques
    toast.success('Rappels téléphoniques : 2 patients à contacter aujourd\'hui');
    // Optionnel: naviguer vers une page spécifique
    // navigate('/patients?filter=reminders');
  };

  useEffect(() => {
    fetchDashboardData();
    fetchBirthdays();
    fetchPhoneReminders();
    fetchMessages();
    initializeWebSocket();
    
    // Cleanup WebSocket on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const initializeWebSocket = () => {
    // Use the backend URL for WebSocket connection
    const backendUrl = new URL(API_BASE_URL);
    const wsProtocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${backendUrl.host}/ws`;
    
    try {
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (ws && ws.readyState === WebSocket.CLOSED) {
            initializeWebSocket();
          }
        }, 3000);
      };
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'new_message':
        setMessages(prev => [...prev, data.data]);
        // Play notification sound for received messages
        if (data.data.sender_type !== user.type) {
          playNotificationSound();
        }
        break;
      case 'message_updated':
        setMessages(prev => prev.map(msg => 
          msg.id === data.data.id ? data.data : msg
        ));
        break;
      case 'message_deleted':
        setMessages(prev => prev.filter(msg => msg.id !== data.data.id));
        break;
      case 'message_read':
        setMessages(prev => prev.map(msg => 
          msg.id === data.data.id ? { ...msg, is_read: true } : msg
        ));
        break;
      case 'messages_cleared':
        setMessages([]);
        toast.success('Messages automatiquement nettoyés');
        break;
      default:
        break;
    }
  };

  const playNotificationSound = () => {
    try {
      // Create a simple notification sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.log('Could not play notification sound:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const fetchBirthdays = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard/birthdays`);
      setBirthdays(response.data.birthdays || []);
    } catch (error) {
      console.error('Error fetching birthdays:', error);
    }
  };

  const fetchPhoneReminders = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard/phone-reminders`);
      setPhoneReminders(response.data.reminders || []);
    } catch (error) {
      console.error('Error fetching phone reminders:', error);
    }
  };

  const viewPatientDetails = async (patientId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients/${patientId}`);
      setSelectedPatient(response.data);
      setShowPatientModal(true);
    } catch (error) {
      console.error('Error fetching patient details:', error);
      toast.error('Erreur lors du chargement des détails du patient');
    }
  };

  const viewConsultationDetails = async (consultationId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/consultations/${consultationId}`);
      setSelectedConsultation(response.data);
      setShowConsultationModal(true);
    } catch (error) {
      console.error('Error fetching consultation details:', error);
      toast.error('Erreur lors du chargement des détails de la consultation');
    }
  };

  const sendWhatsAppBirthday = (patient) => {
    if (patient.numero_whatsapp) {
      const message = `Joyeux anniversaire ${patient.prenom} ! 🎉 Nous vous souhaitons une merveilleuse journée pour vos ${patient.age} ans. L'équipe du cabinet vous adresse ses meilleurs vœux ! 🎂`;
      const whatsappUrl = `https://wa.me/${patient.numero_whatsapp}?text=${encodeURIComponent(message)}`;
      window.open(whatsappUrl, '_blank');
    } else {
      toast.error('Numéro WhatsApp non disponible pour ce patient');
    }
  };

  const sendWhatsAppReminder = (reminder) => {
    if (reminder.numero_whatsapp) {
      const message = `Bonjour ${reminder.patient_prenom}, nous vous contactons pour le suivi de votre consultation du ${new Date(reminder.date_rdv).toLocaleDateString('fr-FR')}. Merci de nous rappeler pour planifier votre prochain rendez-vous si nécessaire.`;
      const whatsappUrl = `https://wa.me/${reminder.numero_whatsapp}?text=${encodeURIComponent(message)}`;
      window.open(whatsappUrl, '_blank');
    } else {
      toast.error('Numéro WhatsApp non disponible pour ce patient');
    }
  };

  // ==================== MESSAGING FUNCTIONS ====================

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/messages`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      const messageData = {
        content: newMessage.trim(),
        reply_to: replyingTo?.id || null
      };

      await axios.post(`${API_BASE_URL}/api/messages`, messageData, {
        params: {
          sender_type: user.type,
          sender_name: user.name
        }
      });

      setNewMessage('');
      setReplyingTo(null);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Erreur lors de l\'envoi du message');
    }
  };

  const handleReplyToMessage = (message) => {
    setReplyingTo(message);
    // Mark message as read when replying
    markMessageAsRead(message.id);
  };

  const handleEditMessage = (message) => {
    setEditingMessage(message);
    setEditingContent(message.content);
  };

  const handleSaveEdit = async () => {
    if (!editingContent.trim()) return;

    try {
      await axios.put(
        `${API_BASE_URL}/api/messages/${editingMessage.id}`,
        { content: editingContent.trim() },
        {
          params: { user_type: user.type }
        }
      );

      setEditingMessage(null);
      setEditingContent('');
    } catch (error) {
      console.error('Error editing message:', error);
      toast.error('Erreur lors de la modification du message');
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/messages/${messageId}`, {
        params: { user_type: user.type }
      });
    } catch (error) {
      console.error('Error deleting message:', error);
      toast.error('Erreur lors de la suppression du message');
    }
  };

  const markMessageAsRead = async (messageId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/messages/${messageId}/read`);
    } catch (error) {
      console.error('Error marking message as read:', error);
    }
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div>
          <h1 className="responsive-title font-bold text-gray-900">
            Bonjour {user.name} 👋
          </h1>
          <p className="text-primary-100 responsive-text">
            Voici un aperçu de votre journée
          </p>
        </div>
      </div>

      {/* Stats Grid - Responsive */}
      <div className="responsive-grid-stats mb-4 sm:mb-6">
        <StatCard
          icon={Calendar}
          title="RDV Aujourd'hui"
          value={stats.total_rdv}
          color="text-blue-600"
          subtitle="Total des rendez-vous"
        />
        <StatCard
          icon={Clock}
          title="Salle attente"
          value={stats.rdv_attente}
          color="text-yellow-600"
          subtitle="Patients en salle d'attente"
        />
        <StatCard
          icon={Users}
          title="Patients Restants"
          value={stats.rdv_restants}
          color="text-orange-600"
          subtitle="Non encore arrivés"
        />
        <StatCard
          icon={Clock}
          title="Temps d'attente"
          value={`${stats.duree_attente_moyenne} min`}
          color="text-teal-600"
          subtitle="Temps d'attente moyen"
        />
        <StatCard
          icon={DollarSign}
          title="Recette du jour"
          value={`${stats.recette_jour} TND`}
          color="text-purple-600"
          subtitle="Paiements encaissés"
        />
      </div>

      {/* Messages and Quick Actions - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* Rappels et alertes */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Rappels et alertes</h3>
          </div>
          
          <div className="space-y-4">
            {/* Anniversaires */}
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Gift className="w-4 h-4 text-pink-500" />
                <h4 className="font-medium text-gray-900">Anniversaires du jour</h4>
                <span className="bg-pink-100 text-pink-600 text-xs px-2 py-1 rounded-full">
                  {birthdays.length}
                </span>
              </div>
              
              {birthdays.length > 0 ? (
                <div className="space-y-2">
                  {birthdays.map((birthday) => (
                    <div key={birthday.id} className="p-3 bg-pink-50 border-l-4 border-pink-400 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <button 
                            onClick={() => viewPatientDetails(birthday.id)}
                            className="font-medium text-primary-600 hover:text-primary-800 underline cursor-pointer"
                          >
                            {birthday.prenom} {birthday.nom}
                          </button>
                          <span className="text-sm text-gray-600 ml-2">- {birthday.age} ans</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => sendWhatsAppBirthday(birthday)}
                            className="text-green-600 hover:text-green-700 p-1"
                            title="Envoyer message WhatsApp"
                          >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.515z"/>
                            </svg>
                          </button>
                          <button
                            className="text-blue-600 hover:text-blue-700 p-1"
                            title="Envoyer SMS (à venir)"
                          >
                            <MessageSquare className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">Aucun anniversaire aujourd'hui</p>
              )}
            </div>

            {/* Relances téléphoniques */}
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <PhoneCall className="w-4 h-4 text-blue-500" />
                <h4 className="font-medium text-gray-900">Relances téléphoniques</h4>
                <span className="bg-blue-100 text-blue-600 text-xs px-2 py-1 rounded-full">
                  {phoneReminders.length}
                </span>
              </div>
              
              {phoneReminders.length > 0 ? (
                <div className="space-y-2">
                  {phoneReminders.map((reminder) => (
                    <div key={reminder.id} className="p-3 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <button 
                            onClick={() => viewPatientDetails(reminder.patient_id)}
                            className="font-medium text-primary-600 hover:text-primary-800 underline cursor-pointer"
                          >
                            {reminder.patient_prenom} {reminder.patient_nom}
                          </button>
                          <p className="text-sm text-gray-600">
                            {reminder.raison_relance} - RDV du {new Date(reminder.date_rdv).toLocaleDateString('fr-FR')}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          {reminder.consultation_id && (
                            <button
                              onClick={() => viewConsultationDetails(reminder.consultation_id)}
                              className="text-indigo-600 hover:text-indigo-700 p-1"
                              title="Voir la consultation"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => sendWhatsAppReminder(reminder)}
                            className="text-green-600 hover:text-green-700 p-1"
                            title="Envoyer rappel WhatsApp"
                          >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.515z"/>
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">Aucune relance programmée</p>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Actions Rapides</h3>
          <div className="space-y-2 sm:space-y-3">
            <button 
              onClick={handleAddPatient}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Users className="w-4 h-4 sm:w-5 sm:h-5 text-primary-600" />
                <span className="font-medium text-primary-900 responsive-text">Ajouter un patient</span>
              </div>
              <div className="text-primary-600">→</div>
            </button>
            
            <button 
              onClick={handleNewAppointment}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-secondary-600" />
                <span className="font-medium text-secondary-900 responsive-text">Nouveau RDV</span>
              </div>
              <div className="text-secondary-600">→</div>
            </button>
            
            <button 
              onClick={handlePhoneReminders}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Phone className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
                <span className="font-medium text-green-900 responsive-text">Rappels téléphoniques</span>
              </div>
              <div className="text-green-600">→</div>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity - Responsive */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Messagerie Interne</h3>
        
        {/* Messages Container */}
        <div className="flex flex-col h-96">
          {/* Messages List */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-3 bg-gray-50 rounded-lg p-3">
            {messages.length > 0 ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.sender_type === user.type ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender_type === user.type
                        ? 'bg-primary-500 text-white'
                        : message.sender_type === 'medecin'
                        ? 'bg-green-100 text-green-900 border-l-4 border-green-500'
                        : 'bg-blue-100 text-blue-900 border-l-4 border-blue-500'
                    }`}
                  >
                    {/* Reply indicator */}
                    {message.reply_to && (
                      <div className="text-xs opacity-75 mb-1 italic">
                        En réponse à: "{message.reply_content.substring(0, 30)}..."
                      </div>
                    )}
                    
                    {/* Message content */}
                    <div className="text-sm">{message.content}</div>
                    
                    {/* Message footer */}
                    <div className="flex justify-between items-center mt-2 text-xs opacity-75">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">
                          {message.sender_type === 'medecin' ? '👨‍⚕️' : '👩‍💼'} {message.sender_name}
                        </span>
                        {message.is_edited && (
                          <span className="text-xs italic">(modifié)</span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <span>
                          {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                        {message.sender_type === user.type && (
                          <div className="flex space-x-1 ml-2">
                            <button
                              onClick={() => handleEditMessage(message)}
                              className="text-xs hover:opacity-100 opacity-60"
                              title="Modifier"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeleteMessage(message.id)}
                              className="text-xs hover:opacity-100 opacity-60"
                              title="Supprimer"
                            >
                              🗑️
                            </button>
                          </div>
                        )}
                        {message.sender_type !== user.type && (
                          <button
                            onClick={() => handleReplyToMessage(message)}
                            className="text-xs hover:opacity-100 opacity-60 ml-2"
                            title="Répondre"
                          >
                            ↩️
                          </button>
                        )}
                        {!message.is_read && message.sender_type !== user.type && (
                          <span className="w-2 h-2 bg-red-500 rounded-full ml-1" title="Non lu"></span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Aucun message aujourd'hui</p>
                <p className="text-xs text-gray-400 mt-1">Commencez une conversation</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Reply indicator */}
          {replyingTo && (
            <div className="mb-2 p-2 bg-gray-100 rounded-lg text-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">
                  Réponse à {replyingTo.sender_name}: "{replyingTo.content.substring(0, 50)}..."
                </span>
                <button
                  onClick={() => setReplyingTo(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Message Input */}
          <div className="flex space-x-2">
            {editingMessage ? (
              <>
                <input
                  type="text"
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                  placeholder="Modifier le message..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveEdit();
                    }
                  }}
                />
                <button
                  onClick={handleSaveEdit}
                  className="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm"
                >
                  ✓
                </button>
                <button
                  onClick={() => {
                    setEditingMessage(null);
                    setEditingContent('');
                  }}
                  className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 text-sm"
                >
                  ✕
                </button>
              </>
            ) : (
              <>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                  placeholder={
                    replyingTo
                      ? `Répondre à ${replyingTo.sender_name}...`
                      : "Tapez votre message..."
                  }
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSendMessage();
                    }
                  }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim()}
                  className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  <MessageSquare className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Consultation Details Modal */}
      {showConsultationModal && selectedConsultation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Consultation - {selectedConsultation.patient?.prenom} {selectedConsultation.patient?.nom}
                </h2>
                <button
                  onClick={() => setShowConsultationModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Informations générales */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations générales</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date:</span>
                      <p className="text-gray-900">
                        {selectedConsultation.appointment?.date ? 
                          new Date(selectedConsultation.appointment.date).toLocaleDateString('fr-FR') : 
                          new Date(selectedConsultation.date).toLocaleDateString('fr-FR')
                        }
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Heure:</span>
                      <p className="text-gray-900">{selectedConsultation.appointment?.heure || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Type:</span>
                      <p className="text-gray-900">{selectedConsultation.appointment?.type_rdv || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Motif:</span>
                      <p className="text-gray-900">{selectedConsultation.appointment?.motif || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Durée:</span>
                      <p className="text-gray-900">{selectedConsultation.duree || 0} minutes</p>
                    </div>
                  </div>
                </div>

                {/* Informations patient */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Patient</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Nom:</span>
                      <p className="text-gray-900">
                        {selectedConsultation.patient?.prenom} {selectedConsultation.patient?.nom}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Âge:</span>
                      <p className="text-gray-900">{selectedConsultation.patient?.age || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Mesures */}
                {(selectedConsultation.poids || selectedConsultation.taille) && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                    <div className="space-y-3">
                      {selectedConsultation.poids && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Poids:</span>
                          <p className="text-gray-900">{selectedConsultation.poids} kg</p>
                        </div>
                      )}
                      {selectedConsultation.taille && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Taille:</span>
                          <p className="text-gray-900">{selectedConsultation.taille} cm</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Observations et bilan */}
                <div className="lg:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Consultation</h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Observations:</span>
                      <div className="mt-1 p-3 bg-gray-50 rounded-lg">
                        <p className="text-gray-900 whitespace-pre-wrap">
                          {selectedConsultation.observations || 'Aucune observation'}
                        </p>
                      </div>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Bilan/Traitement:</span>
                      <div className="mt-1 p-3 bg-gray-50 rounded-lg">
                        <p className="text-gray-900 whitespace-pre-wrap">
                          {selectedConsultation.bilan || selectedConsultation.traitement || 'Aucun bilan'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowConsultationModal(false)}
                  className="btn-outline"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Patient Details Modal */}
      {showPatientModal && selectedPatient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Fiche Patient - {selectedPatient.prenom} {selectedPatient.nom}
                </h2>
                <button
                  onClick={() => setShowPatientModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <span className="sr-only">Fermer</span>
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations personnelles</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Nom complet:</span>
                      <p className="text-gray-900">{selectedPatient.prenom} {selectedPatient.nom}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Âge:</span>
                      <p className="text-gray-900">{selectedPatient.age || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date de naissance:</span>
                      <p className="text-gray-900">{selectedPatient.date_naissance || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Adresse:</span>
                      <p className="text-gray-900">{selectedPatient.adresse || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Parents</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-700">Père</h4>
                      <p className="text-gray-900">{selectedPatient.pere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.telephone || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.fonction || 'N/A'}</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-700">Mère</h4>
                      <p className="text-gray-900">{selectedPatient.mere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.telephone || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.fonction || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                <div className="md:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations médicales</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Notes:</span>
                      <p className="text-gray-900 mt-1">{selectedPatient.notes || 'Aucune note'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Antécédents:</span>
                      <p className="text-gray-900 mt-1">{selectedPatient.antecedents || 'Aucun antécédent'}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowPatientModal(false)}
                  className="btn-outline"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;