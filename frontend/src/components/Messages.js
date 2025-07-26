import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Search, 
  Send, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  User, 
  Phone,
  MessageCircle,
  Eye,
  X,
  Filter,
  FileText,
  Edit2,
  Save,
  Trash2
} from 'lucide-react';
import toast from 'react-hot-toast';

const Messages = ({ user }) => {
  // States
  const [phoneMessages, setPhoneMessages] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [messageContent, setMessageContent] = useState('');
  const [priority, setPriority] = useState('normal');
  const [responseContent, setResponseContent] = useState('');
  const [respondingTo, setRespondingTo] = useState(null);
  
  // Direction filter for bidirectional messages
  const [directionFilter, setDirectionFilter] = useState('');
  
  // Edition
  const [editingMessage, setEditingMessage] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [editPriority, setEditPriority] = useState('normal');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  
  // Modals
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedPatientDetails, setSelectedPatientDetails] = useState(null);
  
  // WebSocket
  const wsRef = useRef(null);

  // Load phone messages
  const loadPhoneMessages = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (priorityFilter) params.append('priority', priorityFilter);
      if (directionFilter) params.append('direction', directionFilter);
      
      const response = await axios.get(`/api/phone-messages?${params}`);
      setPhoneMessages(response.data.phone_messages || []);
    } catch (error) {
      console.error('Error loading phone messages:', error);
      toast.error('Erreur lors du chargement des messages');
    }
  };

  // Search patients
  const searchPatients = async (query) => {
    if (!query) {
      setPatients([]);
      return;
    }
    
    try {
      const response = await axios.get(`/api/patients/search?q=${encodeURIComponent(query)}`);
      setPatients(response.data.patients || []);
    } catch (error) {
      console.error('Error searching patients:', error);
    }
  };

  // Create phone message (bidirectional)
  const handleCreateMessage = async () => {
    if (!messageContent.trim()) {
      toast.error('Veuillez saisir un message');
      return;
    }

    // Determine direction and validation based on user role
    let direction, recipient_role;
    
    if (user.role === 'secretaire') {
      // Secretary sending to doctor
      if (!selectedPatient) {
        toast.error('Veuillez sélectionner un patient');
        return;
      }
      direction = 'secretary_to_doctor';
      recipient_role = 'medecin';
    } else {
      // Doctor sending to secretary
      direction = 'doctor_to_secretary';
      recipient_role = 'secretaire';
    }

    try {
      const now = new Date();
      const messageData = {
        message_content: messageContent,
        priority: priority,
        call_date: now.toISOString().split('T')[0],
        call_time: now.toTimeString().split(' ')[0].substring(0, 5),
        direction: direction,
        recipient_role: recipient_role
      };

      // Add patient_id only for secretary-to-doctor messages
      if (user.role === 'secretaire' && selectedPatient) {
        messageData.patient_id = selectedPatient.id;
      }

      await axios.post('/api/phone-messages', messageData);

      const successMessage = user.role === 'secretaire' 
        ? 'Message envoyé au médecin avec succès'
        : 'Message envoyé à la secrétaire avec succès';
      
      toast.success(successMessage);
      
      // Reset form
      setSelectedPatient(null);
      setMessageContent('');
      setPriority('normal');
      setSearchQuery('');
      setPatients([]);
      
      // Reload messages
      loadPhoneMessages();
    } catch (error) {
      console.error('Error creating phone message:', error);
      toast.error('Erreur lors de la création du message');
    }
  };

  // Respond to phone message (médecin only)
  const handleRespond = async (messageId) => {
    if (!responseContent.trim()) {
      toast.error('Veuillez saisir une réponse');
      return;
    }

    try {
      await axios.put(`/api/phone-messages/${messageId}/response`, {
        response_content: responseContent
      });

      toast.success('Réponse envoyée avec succès');
      setRespondingTo(null);
      setResponseContent('');
      loadPhoneMessages();
    } catch (error) {
      console.error('Error responding to phone message:', error);
      toast.error('Erreur lors de l\'envoi de la réponse');
    }
  };

  // View patient details
  const viewPatientDetails = async (patientId) => {
    try {
      const response = await axios.get(`/api/patients/${patientId}`);
      setSelectedPatientDetails(response.data);
      setShowPatientModal(true);
    } catch (error) {
      console.error('Error loading patient details:', error);
      toast.error('Erreur lors du chargement des détails du patient');
    }
  };

  // Navigate to consultation page for patient
  const viewPatientConsultations = (patientId, patientName) => {
    // Navigate to consultation page with patient pre-selected
    const params = new URLSearchParams({
      patient: patientId,
      patientName: patientName || ''
    });
    window.location.href = `/consultation?${params.toString()}`;
  };

  // Edit phone message
  const handleEditMessage = (message) => {
    setEditingMessage(message);
    setEditContent(message.message_content);
    setEditPriority(message.priority);
  };

  // Save edited message
  const handleSaveEdit = async () => {
    if (!editContent.trim()) {
      toast.error('Le contenu du message ne peut pas être vide');
      return;
    }

    try {
      await axios.put(`/api/phone-messages/${editingMessage.id}`, {
        message_content: editContent,
        priority: editPriority
      });

      toast.success('Message modifié avec succès');
      setEditingMessage(null);
      setEditContent('');
      setEditPriority('normal');
      loadPhoneMessages();
    } catch (error) {
      console.error('Error editing message:', error);
      toast.error('Erreur lors de la modification du message');
    }
  };

  // Cancel edit
  const handleCancelEdit = () => {
    setEditingMessage(null);
    setEditContent('');
    setEditPriority('normal');
  };

  // Delete individual message
  const handleDeleteMessage = async (messageId, patientName) => {
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer ce message de ${patientName} ?\n\nCette action est irréversible.`
    );
    
    if (!confirmed) return;
    
    try {
      await axios.delete(`/api/phone-messages/${messageId}`);
      toast.success('Message supprimé avec succès');
      await loadPhoneMessages(); // Reload messages
    } catch (error) {
      console.error('Error deleting message:', error);
      toast.error('Erreur lors de la suppression du message');
    }
  };

  // Delete all messages
  const handleDeleteAllMessages = async () => {
    const confirmed = window.confirm(
      `🗑️ SUPPRIMER TOUS LES MESSAGES\n\nÊtes-vous sûr de vouloir supprimer TOUS les messages téléphoniques ?\n\nCette action est IRRÉVERSIBLE.\n\n⚠️ Cliquez OK pour confirmer la suppression.`
    );
    
    if (!confirmed) return;
    
    try {
      const response = await axios.delete('/api/phone-messages');
      toast.success(response.data.message);
      await loadPhoneMessages(); // Reload messages
    } catch (error) {
      console.error('Error deleting all messages:', error);
      toast.error('Erreur lors de la suppression des messages');
    }
  };

  // Initialize component
  useEffect(() => {
    loadPhoneMessages();
    setLoading(false);

    // Setup WebSocket for real-time notifications
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    const wsUrl = backendUrl.replace(/^http/, 'ws') + '/api/ws';
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_phone_message' || data.type === 'phone_message_responded') {
        loadPhoneMessages();
        
        // Show notification
        if (data.type === 'new_phone_message') {
          if (data.direction === 'secretary_to_doctor' && user.role === 'medecin') {
            toast.success(`Nouveau message de la secrétaire concernant ${data.patient_name}`, {
              icon: '📞',
              duration: 5000
            });
          } else if (data.direction === 'doctor_to_secretary' && user.role === 'secretaire') {
            toast.success(`Nouveau message du médecin`, {
              icon: '📞',
              duration: 5000
            });
          }
        } else if (data.type === 'phone_message_responded') {
          if (data.direction === 'secretary_to_doctor' && user.role === 'secretaire') {
            toast.success(`Réponse reçue du médecin concernant ${data.patient_name}`, {
              icon: '✅',
              duration: 5000
            });
          } else if (data.direction === 'doctor_to_secretary' && user.role === 'medecin') {
            toast.success(`Réponse reçue de la secrétaire`, {
              icon: '✅',
              duration: 5000
            });
          }
        }
      }
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user.type]);

  // Reload when filters change
  useEffect(() => {
    loadPhoneMessages();
  }, [statusFilter, priorityFilter, directionFilter]);

  // Search patients when search query changes
  useEffect(() => {
    const timer = setTimeout(() => {
      searchPatients(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Phone className="w-6 h-6 mr-2 text-primary-500" />
            Messages Téléphoniques
          </h1>
          <p className="text-gray-600">
            {user.role === 'secretaire' 
              ? 'Transmettez les messages des patients au médecin'
              : 'Consultez et répondez aux messages des patients'
            }
          </p>
        </div>
        
        {/* Delete All Messages Button */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleDeleteAllMessages}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
            title="Supprimer tous les messages"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">Effacer tout</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Message Creation (both roles) */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <MessageCircle className="w-5 h-5 mr-2 text-blue-500" />
              {user.role === 'secretaire' ? 'Message au Médecin' : 'Message à la Secrétaire'}
            </h2>

            {/* Patient Search (only for secretary) */}
            {user.role === 'secretaire' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rechercher un patient
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Nom du patient..."
                  />
                </div>

                {/* Patient Search Results */}
                {patients.length > 0 && (
                  <div className="mt-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg bg-white">
                    {patients.map((patient) => (
                      <div
                        key={patient.id}
                        onClick={() => {
                          setSelectedPatient(patient);
                          setSearchQuery(`${patient.prenom} ${patient.nom}`);
                          setPatients([]);
                        }}
                        className="px-4 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">
                          {patient.prenom} {patient.nom}
                        </div>
                        <div className="text-sm text-gray-500">
                          {patient.age} - {patient.numero_whatsapp}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Selected Patient */}
                {selectedPatient && (
                  <div className="mt-2 p-3 bg-primary-50 rounded-lg border border-primary-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-primary-900">
                          {selectedPatient.prenom} {selectedPatient.nom}
                        </div>
                        <div className="text-sm text-primary-600">
                          {selectedPatient.age}
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedPatient(null);
                          setSearchQuery('');
                        }}
                        className="text-primary-600 hover:text-primary-800"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Message Content */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {user.role === 'secretaire' ? 'Question du patient' : 'Message pour la secrétaire'}
              </label>
              <textarea
                value={messageContent}
                onChange={(e) => setMessageContent(e.target.value)}
                className="textarea-stylus"
                rows={4}
                placeholder={user.role === 'secretaire' 
                  ? "Décrivez la question ou demande du patient - Optimisé pour Apple Pencil"
                  : "Votre message pour la secrétaire - Optimisé pour Apple Pencil"
                }
                inputMode="text"
                autoCapitalize="sentences"
              />
            </div>

            {/* Priority */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priorité
              </label>
              <div className="flex space-x-3">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="normal"
                    checked={priority === 'normal'}
                    onChange={(e) => setPriority(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Normal</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="urgent"
                    checked={priority === 'urgent'}
                    onChange={(e) => setPriority(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-sm text-red-700 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    Urgent
                  </span>
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleCreateMessage}
              disabled={!messageContent.trim() || (user.role === 'secretaire' && !selectedPatient)}
              className={`w-full flex items-center justify-center py-2 px-4 rounded-lg font-medium transition-colors ${
                messageContent.trim() && (user.role === 'medecin' || selectedPatient)
                  ? 'bg-primary-500 text-white hover:bg-primary-600'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Send className="w-4 h-4 mr-2" />
              {user.role === 'secretaire' ? 'Envoyer au Médecin' : 'Envoyer à la Secrétaire'}
            </button>
          </div>
        </div>

        {/* Right Column - Messages List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            {/* Messages Header with Filters */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Messages ({phoneMessages.length})
                </h2>
                
                <div className="flex space-x-3">
                  {/* Direction Filter */}
                  <select
                    value={directionFilter}
                    onChange={(e) => setDirectionFilter(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">Toutes directions</option>
                    <option value="secretary_to_doctor">Secrétaire → Médecin</option>
                    <option value="doctor_to_secretary">Médecin → Secrétaire</option>
                  </select>
                  
                  {/* Status Filter */}
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">Tous les statuts</option>
                    <option value="nouveau">Nouveau</option>
                    <option value="traité">Traité</option>
                  </select>
                  
                  {/* Priority Filter */}
                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">Toutes priorités</option>
                    <option value="urgent">Urgent</option>
                    <option value="normal">Normal</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Messages List */}
            <div className="max-h-96 overflow-y-auto">
              {phoneMessages.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Phone className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p className="font-medium">Aucun message téléphonique</p>
                  <p className="text-sm">Les messages apparaîtront ici</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {phoneMessages.map((message) => (
                    <div key={message.id} className="p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {/* Message Header with Direction */}
                          <div className="flex items-center mb-2">
                            {/* Direction Badge */}
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mr-2 ${
                              message.direction === 'secretary_to_doctor' 
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {message.direction === 'secretary_to_doctor' ? '📝 Secrétaire → Médecin' : '👨‍⚕️ Médecin → Secrétaire'}
                            </span>
                            
                            {/* Patient Name (only for secretary-to-doctor messages) */}
                            {message.patient_name && (
                              <button
                                onClick={() => viewPatientDetails(message.patient_id)}
                                className="font-medium text-primary-600 hover:text-primary-800 underline"
                              >
                                {message.patient_name}
                              </button>
                            )}
                            
                            {/* Priority Badge */}
                            {message.priority === 'urgent' && (
                              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                Urgent
                              </span>
                            )}
                            
                            {/* Status Badge */}
                            <span className={`ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              message.status === 'nouveau' 
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {message.status === 'nouveau' ? (
                                <>
                                  <Clock className="w-3 h-3 mr-1" />
                                  Nouveau
                                </>
                              ) : (
                                <>
                                  <CheckCircle2 className="w-3 h-3 mr-1" />
                                  Traité
                                </>
                              )}
                            </span>
                          </div>

                          {/* Message Content */}
                          <div className="mb-2">
                            {editingMessage && editingMessage.id === message.id ? (
                              /* Edit Mode */
                              <div className="space-y-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <div className="flex items-center mb-2">
                                  <Edit2 className="w-4 h-4 text-yellow-600 mr-2" />
                                  <span className="font-medium text-yellow-800">Modification du message:</span>
                                </div>
                                
                                <textarea
                                  value={editContent}
                                  onChange={(e) => setEditContent(e.target.value)}
                                  className="textarea-stylus text-sm"
                                  rows={3}
                                  placeholder="Contenu du message - Optimisé pour Apple Pencil"
                                  inputMode="text"
                                  autoCapitalize="sentences"
                                />
                                
                                <div className="flex items-center space-x-4">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium text-gray-700">Priorité:</span>
                                    <label className="flex items-center">
                                      <input
                                        type="radio"
                                        value="normal"
                                        checked={editPriority === 'normal'}
                                        onChange={(e) => setEditPriority(e.target.value)}
                                        className="mr-1"
                                      />
                                      <span className="text-sm">Normal</span>
                                    </label>
                                    <label className="flex items-center">
                                      <input
                                        type="radio"
                                        value="urgent"
                                        checked={editPriority === 'urgent'}
                                        onChange={(e) => setEditPriority(e.target.value)}
                                        className="mr-1"
                                      />
                                      <span className="text-sm text-red-700 flex items-center">
                                        <AlertTriangle className="w-3 h-3 mr-1" />
                                        Urgent
                                      </span>
                                    </label>
                                  </div>
                                </div>
                                
                                <div className="flex items-center space-x-2">
                                  <button
                                    onClick={handleSaveEdit}
                                    disabled={!editContent.trim()}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors flex items-center ${
                                      editContent.trim()
                                        ? 'bg-green-500 text-white hover:bg-green-600'
                                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    }`}
                                  >
                                    <Save className="w-3 h-3 mr-1" />
                                    Sauvegarder
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className="px-3 py-1 bg-gray-500 text-white rounded-lg hover:bg-gray-600 text-sm font-medium"
                                  >
                                    Annuler
                                  </button>
                                </div>
                              </div>
                            ) : (
                              /* View Mode */
                              <p className="text-gray-900 text-sm leading-relaxed">
                                {message.message_content}
                              </p>
                            )}
                          </div>

                          {/* Response Content */}
                          {message.response_content && (
                            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                              <div className="flex items-center mb-1">
                                <User className="w-4 h-4 text-green-600 mr-1" />
                                <span className="text-sm font-medium text-green-800">
                                  {message.direction === 'secretary_to_doctor' 
                                    ? 'Réponse du médecin:'
                                    : 'Réponse de la secrétaire:'
                                  }
                                </span>
                              </div>
                              <p className="text-sm text-green-700">
                                {message.response_content}
                              </p>
                            </div>
                          )}

                          {/* Time and Date */}
                          <div className="mt-2 text-xs text-gray-500">
                            {message.direction === 'secretary_to_doctor' ? 'Appel' : 'Message'} le {new Date(message.call_date).toLocaleDateString('fr-FR')} à {message.call_time}
                            {message.responded_by && (
                              <span className="ml-2">
                                • Répondu par {message.responded_by}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2 ml-4">
                          {/* Delete Button */}
                          <button
                            onClick={() => handleDeleteMessage(message.id, message.patient_name)}
                            className="text-red-600 hover:text-red-700 p-1"
                            title="Supprimer le message"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>

                          {/* Edit Button (for original message creators) */}
                          {!editingMessage && (
                            <button
                              onClick={() => handleEditMessage(message)}
                              className="text-blue-600 hover:text-blue-700 p-1"
                              title="Modifier le message"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}

                          {/* View Patient Consultations - only for messages with patients */}
                          {message.patient_id && (
                            <button
                              onClick={() => viewPatientConsultations(message.patient_id, message.patient_name)}
                              className="text-indigo-600 hover:text-indigo-700 p-1"
                              title="Voir les consultations du patient"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          )}

                          {/* Respond Button */}
                          {message.status === 'nouveau' && !editingMessage && (
                            <>
                              {/* Doctor responds to secretary messages */}
                              {user.role === 'medecin' && message.direction === 'secretary_to_doctor' && (
                                <button
                                  onClick={() => {
                                    setRespondingTo(message);
                                    setResponseContent('');
                                  }}
                                  className="px-3 py-1 bg-primary-500 text-white rounded-lg hover:bg-primary-600 text-xs font-medium"
                                >
                                  Répondre
                                </button>
                              )}
                              
                              {/* Secretary responds to doctor messages */}
                              {user.role === 'secretaire' && message.direction === 'doctor_to_secretary' && (
                                <button
                                  onClick={() => {
                                    setRespondingTo(message);
                                    setResponseContent('');
                                  }}
                                  className="px-3 py-1 bg-primary-500 text-white rounded-lg hover:bg-primary-600 text-xs font-medium"
                                >
                                  Répondre
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      {/* Response Form (when responding) */}
                      {respondingTo && respondingTo.id === message.id && (
                        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <div className="flex items-center mb-2">
                            <FileText className="w-4 h-4 text-blue-600 mr-2" />
                            <span className="font-medium text-blue-800">
                              {message.direction === 'secretary_to_doctor' 
                                ? 'Votre réponse à la secrétaire:'
                                : 'Votre réponse au médecin:'
                              }
                            </span>
                          </div>
                          <textarea
                            value={responseContent}
                            onChange={(e) => setResponseContent(e.target.value)}
                            className="textarea-stylus text-sm"
                            rows={3}
                            placeholder="Rédigez votre réponse - Optimisé pour Apple Pencil"
                            inputMode="text"
                            autoCapitalize="sentences"
                          />
                          <div className="flex items-center space-x-2 mt-3">
                            <button
                              onClick={() => handleRespond(message.id)}
                              disabled={!responseContent.trim()}
                              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                                responseContent.trim()
                                  ? 'bg-green-500 text-white hover:bg-green-600'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              }`}
                            >
                              Envoyer Réponse
                            </button>
                            <button
                              onClick={() => {
                                setRespondingTo(null);
                                setResponseContent('');
                              }}
                              className="px-3 py-1 bg-gray-500 text-white rounded-lg hover:bg-gray-600 text-sm font-medium"
                            >
                              Annuler
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Patient Details Modal */}
      {showPatientModal && selectedPatientDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Fiche Patient - {selectedPatientDetails.prenom} {selectedPatientDetails.nom}
                </h2>
                <button
                  onClick={() => setShowPatientModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations personnelles</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Nom complet:</span>
                      <p className="text-gray-900">{selectedPatientDetails.prenom} {selectedPatientDetails.nom}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Âge:</span>
                      <p className="text-gray-900">{selectedPatientDetails.age || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date de naissance:</span>
                      <p className="text-gray-900">{selectedPatientDetails.date_naissance || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">WhatsApp:</span>
                      <p className="text-gray-900">{selectedPatientDetails.numero_whatsapp || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Parents</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-700">Père</h4>
                      <p className="text-gray-900">{selectedPatientDetails.pere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatientDetails.pere?.telephone || 'N/A'}</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-700">Mère</h4>
                      <p className="text-gray-900">{selectedPatientDetails.mere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatientDetails.mere?.telephone || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between mt-6">
                <button
                  onClick={() => viewPatientConsultations(selectedPatientDetails.id, `${selectedPatientDetails.prenom} ${selectedPatientDetails.nom}`)}
                  className="btn-primary"
                >
                  Voir Consultations
                </button>
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

export default Messages;