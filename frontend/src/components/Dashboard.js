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
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState({ show: false, messageId: null, messageContent: '' });
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
    try {
      // Construct WebSocket URL properly handling both relative and absolute API_BASE_URL
      let wsUrl;
      if (API_BASE_URL.startsWith('http://') || API_BASE_URL.startsWith('https://')) {
        // API_BASE_URL is absolute URL
        const backendUrl = new URL(API_BASE_URL);
        const wsProtocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${wsProtocol}//${backendUrl.host}/api/ws`;
      } else {
        // API_BASE_URL is relative or empty, use current host with /api/ws
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${wsProtocol}//${host}/api/ws`;
      }
      
      console.log('Attempting WebSocket connection to:', wsUrl);
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        setWs(websocket);
        // Only show activation message on first connection, not on reconnections
        if (!ws) {
          toast.success('Messagerie temps réel activée');
        }
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        // Only show error on first connection attempt, not on reconnections
        if (!ws) {
          toast.error('Erreur de connexion messagerie temps réel');
        }
      };
      
      websocket.onclose = (event) => {
        console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
        const wasConnected = ws !== null;
        setWs(null);
        
        // Only attempt reconnection if we were previously connected and the page is still active
        if (wasConnected && !event.wasClean) {
          setTimeout(() => {
            console.log('🔄 Attempting WebSocket reconnection...');
            initializeWebSocket();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      toast.error('Impossible d\'initialiser la messagerie temps réel');
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'new_message':
        // Ne pas ajouter ses propres messages (déjà ajoutés optimistiquement)
        if (data.data.sender_type !== user.type || data.data.sender_name !== user.name) {
          setMessages(prev => [...prev, data.data]);
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
        toast.success(`${data.deleted_count} message(s) supprimé(s)`);
        break;
      default:
        break;
    }
  };

  // Clear all messages
  const handleClearMessages = async () => {
    const confirmed = window.confirm('🗑️ VIDER LE CHAT\n\nÊtes-vous sûr de vouloir supprimer TOUS les messages ?\n\nCette action est IRRÉVERSIBLE.\n\n⚠️ Cliquez OK pour confirmer la suppression.');
    
    if (confirmed) {
      try {
        await axios.delete(`${API_BASE_URL}/api/messages`);
        // Don't show local toast here - WebSocket will handle the notification
        setMessages([]);
      } catch (error) {
        console.error('Error clearing messages:', error);
        toast.error('❌ Erreur lors de la suppression des messages');
      }
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

  const getShortSenderName = (senderName, senderType) => {
    // Abbreviate sender names for messaging interface
    if (senderType === 'medecin') {
      return 'Dr';
    } else if (senderType === 'secretaire') {
      return 'Sec';
    }
    return senderName; // fallback to original name
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/messages`);
      const fetchedMessages = response.data.messages || [];
      
      // Remove any duplicates and sort by timestamp
      const uniqueMessages = fetchedMessages.filter((message, index, self) =>
        index === self.findIndex(m => m.id === message.id)
      ).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      setMessages(uniqueMessages);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const messageData = {
      content: newMessage.trim(),
      reply_to: replyingTo?.id || null
    };

    try {
      // Clear input and reply state immediately for better UX
      const messageContent = newMessage.trim();
      const replyToMessage = replyingTo;
      setNewMessage('');
      setReplyingTo(null);

      // Add message optimistically (immediately) to UI
      const optimisticMessage = {
        id: `temp_${Date.now()}`, // Temporary ID
        sender_type: user.type,
        sender_name: user.name,
        content: messageContent,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_edited: false,
        original_content: "",
        reply_to: replyToMessage?.id || null,
        reply_content: replyToMessage?.content || "",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, optimisticMessage]);

      // Send to server
      const response = await axios.post(`${API_BASE_URL}/api/messages`, messageData, {
        params: {
          sender_type: user.type,
          sender_name: user.name
        }
      });

      // Replace the optimistic message with the real one from server
      const realMessage = response.data;
      setMessages(prev => prev.map(msg => 
        msg.id === optimisticMessage.id ? { ...optimisticMessage, id: realMessage.id } : msg
      ));
      
      console.log('✅ Message sent successfully:', response.data);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Erreur lors de l\'envoi du message');
      
      // Remove the failed optimistic message
      setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp_')));
      
      // Restore the message input if sending failed
      setNewMessage(messageData.content);
      setReplyingTo(messageData.reply_to ? replyingTo : null);
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
      
      // If WebSocket is not connected, fetch messages manually
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log('WebSocket not connected, fetching messages manually after edit');
        await fetchMessages();
      }
    } catch (error) {
      console.error('Error editing message:', error);
      toast.error('Erreur lors de la modification du message');
    }
  };

  const handleDeleteMessage = async (messageId) => {
    console.log('🗑️ Delete button clicked for message:', messageId);
    
    const messageToDelete = messages.find(msg => msg.id === messageId);
    if (!messageToDelete) {
      console.log('❌ Message not found in current messages');
      toast.error('Message introuvable');
      return;
    }
    
    // Show custom confirmation dialog
    setDeleteConfirmDialog({
      show: true,
      messageId: messageId,
      messageContent: messageToDelete.content
    });
  };

  const confirmDelete = async () => {
    const { messageId } = deleteConfirmDialog;
    console.log('🔄 User confirmed deletion, proceeding...');
    
    // Close dialog
    setDeleteConfirmDialog({ show: false, messageId: null, messageContent: '' });
    
    const messageToDelete = messages.find(msg => msg.id === messageId);

    // Suppression optimiste : retirer immédiatement de l'UI
    console.log('🔄 Removing message optimistically:', messageId);
    setMessages(prevMessages => {
      const beforeCount = prevMessages.length;
      const updatedMessages = prevMessages.filter(msg => msg.id !== messageId);
      const afterCount = updatedMessages.length;
      console.log('📊 Messages before:', beforeCount, 'after:', afterCount);
      return updatedMessages;
    });

    try {
      console.log('🔄 Sending DELETE request to server...');
      
      const response = await axios.delete(`${API_BASE_URL}/api/messages/${messageId}`, {
        params: { user_type: user.type }
      });
      
      console.log('✅ Delete request successful:', response.data);
      
      // Show success feedback
      toast.success('Message supprimé avec succès');
      
    } catch (error) {
      console.error('❌ Error deleting message from server:', error);
      
      // En cas d'erreur, restaurer le message dans l'UI
      console.log('🔄 Restoring message due to server error');
      setMessages(prevMessages => {
        const restored = [...prevMessages, messageToDelete].sort((a, b) => 
          new Date(a.timestamp) - new Date(b.timestamp)
        );
        console.log('📊 Messages restored, count:', restored.length);
        return restored;
      });
      
      if (error.response) {
        if (error.response.status === 403) {
          toast.error('Vous ne pouvez supprimer que vos propres messages');
        } else if (error.response.status === 404) {
          toast.error('Message non trouvé');
        } else {
          toast.error(`Erreur: ${error.response.data.detail || 'Erreur inconnue'}`);
        }
      } else {
        toast.error('Erreur lors de la suppression du message');
      }
    }
  };

  const cancelDelete = () => {
    console.log('❌ Delete cancelled by user');
    setDeleteConfirmDialog({ show: false, messageId: null, messageContent: '' });
  };

  const markMessageAsRead = async (messageId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/messages/${messageId}/read`);
    } catch (error) {
      console.error('Error marking message as read:', error);
    }
  };

  // Marquer automatiquement les messages des autres comme lus quand ils sont affichés
  useEffect(() => {
    const unreadMessages = messages.filter(
      msg => !msg.is_read && msg.sender_type !== user.type
    );
    
    unreadMessages.forEach(message => {
      // Marquer comme lu après un délai pour simuler la lecture
      setTimeout(() => {
        markMessageAsRead(message.id);
      }, 2000);
    });
  }, [messages, user.type]);

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

      {/* Custom Delete Confirmation Dialog */}
      {deleteConfirmDialog.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <span className="text-2xl">🗑️</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Supprimer le message
              </h3>
              <p className="text-sm text-gray-500 mb-2">
                Êtes-vous sûr de vouloir supprimer ce message ?
              </p>
              <p className="text-xs text-gray-400 bg-gray-50 p-2 rounded italic mb-4">
                "{deleteConfirmDialog.messageContent.substring(0, 60)}..."
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={cancelDelete}
                  className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={confirmDelete}
                  className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                >
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>
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
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4 flex items-center justify-between">
          <div className="flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-primary-500" />
            Messagerie Interne
          </div>
          <button
            onClick={handleClearMessages}
            className="text-xs px-3 py-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors font-medium border-2 border-red-500 hover:border-red-600 shadow-sm"
            title="Cliquer pour vider tout le chat (avec confirmation)"
          >
            🗑️ VIDER LE CHAT
          </button>
        </h3>
        
        {/* Messages Container */}
        <div className="flex flex-col h-96">
          {/* Messages List */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-3 bg-gradient-to-b from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-100">
            {messages.length > 0 ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.sender_type === user.type ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm relative ${
                      message.sender_type === user.type
                        ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-primary-200'
                        : message.sender_type === 'medecin'
                        ? 'bg-gradient-to-r from-green-100 to-green-50 text-green-900 border border-green-200 shadow-green-100'
                        : 'bg-gradient-to-r from-blue-100 to-blue-50 text-blue-900 border border-blue-200 shadow-blue-100'
                    }`}
                  >
                    {/* Reply indicator */}
                    {message.reply_to && (
                      <div className={`text-xs mb-2 p-2 rounded-lg border-l-3 ${
                        message.sender_type === user.type 
                          ? 'bg-white bg-opacity-20 border-white border-opacity-50 text-white text-opacity-90'
                          : 'bg-white bg-opacity-70 border-gray-400 text-gray-600'
                      }`}>
                        <div className="font-medium text-xs opacity-75">↳ Réponse à</div>
                        <div className="text-xs italic">{message.reply_content.substring(0, 40)}...</div>
                      </div>
                    )}
                    
                    {/* Message content */}
                    <div className="text-sm font-medium leading-relaxed">{message.content}</div>
                    
                    {/* Message footer */}
                    <div className="flex justify-between items-end mt-3 text-xs">
                      <div className="flex items-center space-x-2">
                        <div className={`flex items-center space-x-1 ${
                          message.sender_type === user.type ? 'text-white text-opacity-80' : 'text-gray-600'
                        }`}>
                          <span className="text-sm">
                            {message.sender_type === 'medecin' ? '👨‍⚕️' : '👩‍💼'}
                          </span>
                          <span className="font-medium text-xs">
                            {getShortSenderName(message.sender_name, message.sender_type)}
                          </span>
                        </div>
                        {message.is_edited && (
                          <span className={`text-xs italic px-1.5 py-0.5 rounded-full ${
                            message.sender_type === user.type 
                              ? 'bg-white bg-opacity-20 text-white text-opacity-80'
                              : 'bg-gray-200 text-gray-600'
                          }`}>
                            modifié
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs ${
                          message.sender_type === user.type ? 'text-white text-opacity-70' : 'text-gray-500'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                        
                        {/* Action buttons for own messages */}
                        {message.sender_type === user.type && (
                          <div className="flex space-x-1 ml-2">
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                console.log(`🖱️ EDIT BUTTON CLICKED - Message ID: ${message.id}`);
                                handleEditMessage(message);
                              }}
                              className="p-1 rounded-full hover:bg-white hover:bg-opacity-20 transition-colors"
                              title="Modifier"
                            >
                              <span className="text-xs">✏️</span>
                            </button>
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                console.log(`🗑️ DELETE BUTTON CLICKED - Message ID: ${message.id}`);
                                handleDeleteMessage(message.id);
                              }}
                              className="p-1 rounded-full hover:bg-red-500 hover:bg-opacity-20 transition-colors"
                              title="Supprimer"
                              style={{ pointerEvents: 'auto', zIndex: 10 }}
                            >
                              <span className="text-xs">🗑️</span>
                            </button>
                          </div>
                        )}
                        
                        {/* Reply button for others' messages */}
                        {message.sender_type !== user.type && (
                          <button
                            onClick={() => handleReplyToMessage(message)}
                            className="p-1 rounded-full hover:bg-gray-200 transition-colors"
                            title="Répondre"
                          >
                            <span className="text-xs">↩️</span>
                          </button>
                        )}
                        
                        {/* Read receipt indicator */}
                        {message.sender_type === user.type && (
                          <div className="flex items-center space-x-1">
                            {message.is_read ? (
                              <div className="flex items-center space-x-1 bg-green-100 bg-opacity-80 px-2 py-1 rounded-full" title="Message lu">
                                <div className="text-xs font-semibold text-green-600">VU</div>
                                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                              </div>
                            ) : (
                              <div className="flex items-center space-x-1 bg-white bg-opacity-60 px-2 py-1 rounded-full" title="Message envoyé">
                                <div className="text-xs font-medium text-white text-opacity-90">✓</div>
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* Unread indicator for received messages */}
                        {message.sender_type !== user.type && !message.is_read && (
                          <div className="flex items-center space-x-1 bg-red-100 bg-opacity-80 px-2 py-1 rounded-full animate-pulse" title="Non lu">
                            <div className="text-xs font-semibold text-red-600">NOUVEAU</div>
                            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-12">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm font-medium">Aucun message aujourd'hui</p>
                <p className="text-xs text-gray-400 mt-1">Commencez une conversation</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Reply indicator */}
          {replyingTo && (
            <div className="mb-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-400 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-xs font-medium text-blue-700 mb-1">
                    Réponse à {getShortSenderName(replyingTo.sender_name, replyingTo.sender_type)}
                  </div>
                  <span className="text-sm text-blue-600 italic">
                    "{replyingTo.content.substring(0, 60)}..."
                  </span>
                </div>
                <button
                  onClick={() => setReplyingTo(null)}
                  className="text-blue-400 hover:text-blue-600 p-1 rounded-full hover:bg-blue-100 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Message Input */}
          <div className="border-t border-gray-200 pt-3">
            {editingMessage ? (
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm shadow-sm"
                  placeholder="Modifier le message..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveEdit();
                    }
                  }}
                />
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-3 bg-green-500 text-white rounded-full hover:bg-green-600 shadow-sm transition-colors"
                  title="Sauvegarder"
                >
                  <span className="text-sm">✓</span>
                </button>
                <button
                  onClick={() => {
                    setEditingMessage(null);
                    setEditingContent('');
                  }}
                  className="px-4 py-3 bg-gray-500 text-white rounded-full hover:bg-gray-600 shadow-sm transition-colors"
                  title="Annuler"
                >
                  <span className="text-sm">✕</span>
                </button>
              </div>
            ) : (
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm shadow-sm placeholder-gray-400"
                  placeholder={
                    replyingTo
                      ? `Répondre à ${getShortSenderName(replyingTo.sender_name, replyingTo.sender_type)}...`
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
                  className={`px-5 py-3 rounded-full shadow-sm transition-all duration-200 ${
                    newMessage.trim()
                      ? 'bg-primary-500 text-white hover:bg-primary-600 transform hover:scale-105'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                  title="Envoyer message"
                >
                  <MessageSquare className="w-4 h-4" />
                </button>
              </div>
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