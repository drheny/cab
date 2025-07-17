import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  User, 
  FileText,
  Save,
  Play,
  Pause,
  Square,
  ChevronDown,
  ChevronUp,
  Edit,
  Trash2,
  Eye,
  Stethoscope,
  MapPin,
  Phone,
  Users,
  X,
  MessageCircle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Consultation = ({ user }) => {
  const [activeConsultations, setActiveConsultations] = useState([]);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [expandedPatient, setExpandedPatient] = useState(null);
  const [patientHistory, setPatientHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showConsultationDetailModal, setShowConsultationDetailModal] = useState(false);
  const [selectedConsultationDetail, setSelectedConsultationDetail] = useState(null);
  const [showEditConsultationModal, setShowEditConsultationModal] = useState(false);
  const [editingConsultation, setEditingConsultation] = useState(null);
  const [consultationFormData, setConsultationFormData] = useState({
    observations: '',
    traitement: '',
    bilan: '',
    relance_date: '',
    duree: ''
  });
  const [consultationData, setConsultationData] = useState({
    observations: '',
    traitement: '',
    bilan: '',
    relance_date: ''
  });

  useEffect(() => {
    fetchActiveConsultations();
  }, []);

  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setTimer(timer => timer + 1);
      }, 1000);
    } else if (!isRunning && timer !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRunning, timer]);

  const fetchActiveConsultations = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      console.log('Fetching consultations for date:', today);
      
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/rdv/jour/${today}`);
      console.log('API Response:', response.data);
      
      // Enrichir les données patient pour chaque consultation
      const enrichedConsultations = await Promise.all(
        response.data.map(async (apt) => {
          try {
            const patientResponse = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${apt.patient_id}`);
            return {
              ...apt,
              patient: patientResponse.data
            };
          } catch (error) {
            console.error(`Error fetching patient data for ${apt.patient_id}:`, error);
            return apt; // Retourner l'appointment avec les données patient basiques
          }
        })
      );
      
      console.log('Enriched consultations:', enrichedConsultations);
      
      // Log each appointment status
      enrichedConsultations.forEach((apt, index) => {
        console.log(`Appointment ${index}:`, {
          id: apt.id,
          statut: apt.statut,
          patient: apt.patient?.nom,
          salle: apt.salle,
          patientComplete: apt.patient
        });
      });
      
      // Temporairement, incluons les consultations "attente" et "retard" pour tester le panel expandable
      const inProgressAppointments = enrichedConsultations.filter(apt => 
        apt.statut === 'en_cours' || apt.statut === 'attente' || apt.statut === 'retard'
      );
      console.log('Filtered consultations (includes attente/retard for testing):', inProgressAppointments);
      console.log('Number of en_cours appointments:', inProgressAppointments.length);
      
      setActiveConsultations(inProgressAppointments);
      
      if (inProgressAppointments.length > 0 && !selectedConsultation) {
        setSelectedConsultation(inProgressAppointments[0]);
        console.log('Selected consultation:', inProgressAppointments[0]);
      }
    } catch (error) {
      console.error('Error fetching consultations:', error);
      toast.error('Erreur lors du chargement des consultations');
    } finally {
      setLoading(false);
    }
  };

  const togglePatientExpansion = async (consultation) => {
    if (expandedPatient === consultation.id) {
      setExpandedPatient(null);
      setPatientHistory([]);
    } else {
      setExpandedPatient(consultation.id);
      console.log('Expanding patient:', consultation.patient);
      
      // Charger l'historique des consultations
      await loadPatientHistory(consultation.patient_id);
    }
  };

  const loadPatientHistory = async (patientId) => {
    try {
      setLoadingHistory(true);
      console.log('Loading patient history for:', patientId);
      
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}/consultations`);
      console.log('Patient history loaded:', response.data);
      setPatientHistory(response.data);
    } catch (error) {
      console.error('Error loading patient history:', error);
      toast.error('Erreur lors du chargement de l\'historique');
    } finally {
      setLoadingHistory(false);
    }
  };

  const viewConsultationDetail = (consultation) => {
    setSelectedConsultationDetail(consultation);
    setShowConsultationDetailModal(true);
  };

  const editConsultation = (consultation) => {
    setEditingConsultation(consultation);
    setConsultationFormData({
      observations: consultation.observations || '',
      traitement: consultation.traitement || '',
      bilan: consultation.bilan || '',
      relance_date: consultation.relance_date || '',
      duree: consultation.duree?.toString() || ''
    });
    setShowEditConsultationModal(true);
  };

  const saveConsultation = async () => {
    try {
      if (!editingConsultation) return;
      
      console.log('Editing consultation:', editingConsultation);
      console.log('Form data:', consultationFormData);
      
      const updatedConsultation = {
        ...editingConsultation,
        observations: consultationFormData.observations,
        traitement: consultationFormData.traitement,
        bilan: consultationFormData.bilan,
        relance_date: consultationFormData.relance_date,
        duree: parseInt(consultationFormData.duree) || 0
      };

      console.log('Updated consultation payload:', updatedConsultation);

      const response = await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/consultations/${editingConsultation.id}`, updatedConsultation);
      
      console.log('Update response:', response.data);
      
      toast.success('Consultation mise à jour avec succès');
      setShowEditConsultationModal(false);
      setEditingConsultation(null);
      
      // Refresh patient history
      if (expandedPatient) {
        const consultation = activeConsultations.find(c => c.id === expandedPatient);
        if (consultation) {
          await loadPatientHistory(consultation.patient_id);
        }
      }
    } catch (error) {
      console.error('Error saving consultation:', error);
      console.error('Error response:', error.response?.data);
      toast.error('Erreur lors de la sauvegarde de la consultation');
    }
  };

  const deleteConsultation = async (consultationId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette consultation ?')) {
      try {
        await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/api/consultations/${consultationId}`);
        toast.success('Consultation supprimée avec succès');
        
        // Refresh patient history
        if (expandedPatient) {
          const consultation = activeConsultations.find(c => c.id === expandedPatient);
          if (consultation) {
            await loadPatientHistory(consultation.patient_id);
          }
        }
      } catch (error) {
        console.error('Error deleting consultation:', error);
        toast.error('Erreur lors de la suppression de la consultation');
      }
    }
  };

  const startTimer = () => {
    setIsRunning(true);
  };

  const stopTimer = () => {
    setIsRunning(false);
    // Ne pas remettre à zéro, juste arrêter
  };

  const resetTimer = () => {
    setIsRunning(false);
    setTimer(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const calculateWaitingTime = (appointment) => {
    if (!appointment || !appointment.heure_arrivee_attente) {
      return 'N/A';
    }
    
    try {
      const arrivalTime = new Date(appointment.heure_arrivee_attente);
      const now = new Date();
      const waitingMinutes = Math.floor((now - arrivalTime) / (1000 * 60));
      
      if (waitingMinutes < 0) return '0 min';
      if (waitingMinutes < 60) return `${waitingMinutes} min`;
      
      const hours = Math.floor(waitingMinutes / 60);
      const minutes = waitingMinutes % 60;
      return `${hours}h ${minutes}min`;
    } catch (error) {
      return 'N/A';
    }
  };

  const getSalleDisplayName = (salle) => {
    switch (salle) {
      case 'salle1':
        return 'Salle 1';
      case 'salle2':
        return 'Salle 2';
      case '':
        return 'Aucune salle';
      default:
        return salle || 'N/A';
    }
  };

  const getTypeDisplayName = (type) => {
    switch (type) {
      case 'visite':
        return 'Visite';
      case 'controle':
        return 'Contrôle';
      default:
        return type || 'N/A';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'visite':
        return 'bg-blue-100 text-blue-800';
      case 'controle':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConsultationTypeColor = (type) => {
    switch (type) {
      case 'visite':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'controle':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleSaveConsultation = async () => {
    if (!selectedConsultation) return;

    try {
      // Debug: Log des valeurs du formulaire
      console.log('Données du formulaire avant sauvegarde:', consultationData);
      console.log('Poids:', consultationData.poids, 'Type:', typeof consultationData.poids);
      console.log('Taille:', consultationData.taille, 'Type:', typeof consultationData.taille);
      console.log('PC:', consultationData.pc, 'Type:', typeof consultationData.pc);

      // Debug: Test chaque condition individuellement
      const poidsCondition = consultationData.poids && consultationData.poids.trim() !== '';
      const tailleCondition = consultationData.taille && consultationData.taille.trim() !== '';
      const pcCondition = consultationData.pc && consultationData.pc.trim() !== '';
      
      console.log('Conditions:');
      console.log('- Poids condition:', poidsCondition, '- Valeur:', consultationData.poids);
      console.log('- Taille condition:', tailleCondition, '- Valeur:', consultationData.taille);
      console.log('- PC condition:', pcCondition, '- Valeur:', consultationData.pc);

      const consultationPayload = {
        patient_id: selectedConsultation.patient_id,
        appointment_id: selectedConsultation.id,
        date: new Date().toISOString().split('T')[0],
        duree: Math.floor(timer / 60),
        observations: consultationData.observations || '',
        traitement: consultationData.traitement || '',
        bilan: consultationData.bilan || '',
        relance_date: consultationData.relance_date || ''
      };

      console.log('Payload à envoyer:', JSON.stringify(consultationPayload, null, 2));

      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/consultations`, consultationPayload);
      
      // Mettre à jour le statut du rendez-vous
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/rdv/${selectedConsultation.id}/statut`, { statut: 'termine' });
      
      toast.success('Consultation enregistrée avec succès');
      
      // Reset form
      setConsultationData({
        observations: '',
        traitement: '',
        bilan: '',
        relance_date: ''
      });
      
      resetTimer();
      fetchActiveConsultations();
    } catch (error) {
      console.error('Error saving consultation:', error);
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const handleQuitConsultation = async () => {
    if (!selectedConsultation) return;

    if (window.confirm('Êtes-vous sûr de vouloir quitter cette consultation ?')) {
      try {
        // Remettre le statut à "attente"
        await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/rdv/${selectedConsultation.id}/statut`, { statut: 'attente' });
        
        // Reset form
        setConsultationData({
          observations: '',
          traitement: '',
          bilan: '',
          relance_date: ''
        });
        
        resetTimer();
        toast.success('Consultation annulée');
        fetchActiveConsultations();
      } catch (error) {
        console.error('Error quitting consultation:', error);
        toast.error('Erreur lors de l\'annulation');
      }
    }
  };

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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Consultation</h1>
        <p className="text-gray-600">Suivi des consultations en cours</p>
      </div>

      {activeConsultations.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune consultation en cours
          </h3>
          <p className="text-gray-500">
            Démarrez une consultation depuis les salles d'attente
          </p>
        </div>
      ) : (
        <div className="flex gap-6 min-h-screen">
          {/* Colonne gauche - Consultations actives */}
          <div className="w-80 flex-shrink-0 space-y-4">
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Consultations actives ({activeConsultations.length})
              </h2>
              <div className="space-y-3">
                {activeConsultations.map((consultation) => (
                  <div key={consultation.id} className="space-y-2">
                    <div
                      onClick={() => setSelectedConsultation(consultation)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedConsultation?.id === consultation.id
                          ? 'bg-primary-100 border-primary-200 border-2'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="bg-primary-500 p-2 rounded-full">
                            <User className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {consultation.patient?.prenom} {consultation.patient?.nom}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {consultation.heure} - {getSalleDisplayName(consultation.salle)}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            togglePatientExpansion(consultation);
                          }}
                          className="text-gray-400 hover:text-gray-600 p-1"
                        >
                          {expandedPatient === consultation.id ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Panel expandable */}
                    {expandedPatient === consultation.id && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                        {/* Informations du patient */}
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Informations Patient</h4>
                          <div className="grid grid-cols-1 gap-3 text-sm">
                            <div className="flex items-center space-x-2">
                              <Clock className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-600">Âge:</span>
                              <span className="font-medium">
                                {consultation.patient?.age || 
                                 (consultation.patient?.date_naissance ? 
                                   new Date().getFullYear() - new Date(consultation.patient.date_naissance).getFullYear() : 'N/A')}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <MapPin className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-600">Adresse:</span>
                              <span className="font-medium">{consultation.patient?.adresse || 'N/A'}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Phone className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-600">Téléphone:</span>
                              <span className="font-medium">{consultation.patient?.numero_whatsapp || 'N/A'}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Users className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-600">Père:</span>
                              <span className="font-medium">
                                {consultation.patient?.pere?.nom || 'N/A'}
                                {consultation.patient?.pere?.fonction && ` (${consultation.patient.pere.fonction})`}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Users className="w-4 h-4 text-gray-500" />
                              <span className="text-gray-600">Mère:</span>
                              <span className="font-medium">
                                {consultation.patient?.mere?.nom || 'N/A'}
                                {consultation.patient?.mere?.fonction && ` (${consultation.patient.mere.fonction})`}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <MessageCircle className="w-4 h-4 text-green-500" />
                              <span className="text-gray-600">WhatsApp:</span>
                              {consultation.patient?.numero_whatsapp ? (
                                <a 
                                  href={`https://wa.me/${consultation.patient.numero_whatsapp}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="font-medium text-green-600 hover:text-green-800 underline"
                                >
                                  {consultation.patient.numero_whatsapp}
                                </a>
                              ) : (
                                <span className="font-medium text-gray-400">N/A</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Historique des consultations */}
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Historique des consultations</h4>
                          {loadingHistory ? (
                            <div className="flex items-center justify-center h-16">
                              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
                            </div>
                          ) : (
                            <div className="space-y-2">
                              {patientHistory.length > 0 ? (
                                patientHistory.map((historyItem) => (
                                  <div key={historyItem.id} className="flex items-center justify-between p-2 bg-white rounded border">
                                    <div className="flex items-center space-x-2">
                                      <Stethoscope className="w-3 h-3 text-gray-500" />
                                      <span className="text-sm font-medium">{historyItem.date}</span>
                                      <span className={`text-xs px-2 py-1 rounded-full ${getConsultationTypeColor(historyItem.type)}`}>
                                        {historyItem.type === 'visite' ? 'Visite' : 'Contrôle'}
                                      </span>
                                    </div>
                                    <div className="flex items-center space-x-1">
                                      <button
                                        onClick={() => viewConsultationDetail(historyItem)}
                                        className="text-blue-600 hover:text-blue-800 text-xs"
                                      >
                                        <Eye className="w-3 h-3" />
                                      </button>
                                      <button
                                        onClick={() => editConsultation(historyItem)}
                                        className="text-green-600 hover:text-green-800 text-xs"
                                      >
                                        <Edit className="w-3 h-3" />
                                      </button>
                                      <button
                                        onClick={() => deleteConsultation(historyItem.id)}
                                        className="text-red-600 hover:text-red-800 text-xs"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                      </button>
                                    </div>
                                  </div>
                                ))
                              ) : (
                                <p className="text-sm text-gray-500 text-center py-2">
                                  Aucune consultation dans l'historique
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Contenu principal */}
          <div className="flex-1">
            {selectedConsultation && (
              <div className="space-y-6">
                {/* Bannière améliorée */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Patient Info Section */}
                    <div className="lg:col-span-2">
                      <div className="flex items-start space-x-4">
                        <div className="bg-primary-100 p-3 rounded-full">
                          <User className="w-6 h-6 text-primary-600" />
                        </div>
                        <div className="flex-1">
                          <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            {selectedConsultation.patient?.prenom} {selectedConsultation.patient?.nom}
                          </h2>
                          
                          {/* Appointment Details Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Clock className="w-4 h-4 text-gray-500" />
                                <span className="text-sm text-gray-600">Horaire:</span>
                                <span className="text-sm font-medium text-gray-900">
                                  {selectedConsultation.heure}
                                </span>
                              </div>
                              
                              <div className="flex items-center space-x-2">
                                <div className="w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center">
                                  <span className="text-xs text-white font-bold">W</span>
                                </div>
                                <span className="text-sm text-gray-600">Durée d'attente:</span>
                                <span className="text-sm font-medium text-orange-600">
                                  {calculateWaitingTime(selectedConsultation)}
                                </span>
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <div className="w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center">
                                  <span className="text-xs text-white font-bold">S</span>
                                </div>
                                <span className="text-sm text-gray-600">Salle:</span>
                                <span className="text-sm font-medium text-purple-600">
                                  {getSalleDisplayName(selectedConsultation.salle)}
                                </span>
                              </div>
                              
                              <div className="flex items-center space-x-2">
                                <div className="w-4 h-4 bg-indigo-500 rounded-full flex items-center justify-center">
                                  <span className="text-xs text-white font-bold">T</span>
                                </div>
                                <span className="text-sm text-gray-600">Type:</span>
                                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getTypeColor(selectedConsultation.type_rdv)}`}>
                                  {getTypeDisplayName(selectedConsultation.type_rdv)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Timer Section */}
                    <div className="lg:col-span-1">
                      <div className="text-center bg-gray-50 rounded-lg p-4">
                        <div className="text-2xl font-bold text-primary-600 mb-2">
                          {formatTime(timer)}
                        </div>
                        <p className="text-xs text-gray-500 mb-3">Durée de consultation</p>
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={isRunning ? stopTimer : startTimer}
                            className={`p-2 text-white rounded-lg transition-colors ${
                              isRunning 
                                ? 'bg-red-500 hover:bg-red-600' 
                                : 'bg-green-500 hover:bg-green-600'
                            }`}
                            title={isRunning ? 'Arrêter le chronomètre' : 'Démarrer le chronomètre'}
                          >
                            {isRunning ? (
                              <Square className="w-4 h-4" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Consultation Form */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">
                    Fiche de consultation
                  </h3>

                  <div className="space-y-6">
                    {/* Observations */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Observations cliniques
                      </label>
                      <textarea
                        value={consultationData.observations}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          observations: e.target.value
                        })}
                        className="input-field"
                        rows="4"
                        placeholder="Observations et examens cliniques..."
                      />
                    </div>

                    {/* Traitement */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Traitement prescrit
                      </label>
                      <textarea
                        value={consultationData.traitement}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          traitement: e.target.value
                        })}
                        className="input-field"
                        rows="3"
                        placeholder="Médicaments et posologie..."
                      />
                    </div>

                    {/* Bilan */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Bilan/Examens
                      </label>
                      <textarea
                        value={consultationData.bilan}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          bilan: e.target.value
                        })}
                        className="input-field"
                        rows="3"
                        placeholder="Examens complémentaires demandés..."
                      />
                    </div>

                    {/* Relance */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Date de relance
                      </label>
                      <input
                        type="date"
                        value={consultationData.relance_date}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          relance_date: e.target.value
                        })}
                        className="input-field"
                      />
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={handleQuitConsultation}
                        className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                      >
                        <X className="w-4 h-4" />
                        <span>Quitter consultation</span>
                      </button>
                      <button
                        onClick={handleSaveConsultation}
                        className="btn-primary flex items-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>Enregistrer la consultation</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Consultation Detail Modal */}
      {showConsultationDetailModal && selectedConsultationDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Détails de la consultation
                </h2>
                <button
                  onClick={() => setShowConsultationDetailModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations générales</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date:</span>
                      <p className="text-gray-900">{selectedConsultationDetail.date}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Type:</span>
                      <span className={`ml-2 text-xs px-2 py-1 rounded-full ${getConsultationTypeColor(selectedConsultationDetail.type)}`}>
                        {selectedConsultationDetail.type === 'visite' ? 'Visite' : 'Contrôle'}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Durée:</span>
                      <p className="text-gray-900">{selectedConsultationDetail.duree > 0 ? `${selectedConsultationDetail.duree} minutes` : 'Non spécifiée'}</p>
                    </div>
                  </div>
                </div>

              <div className="mt-6 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Observations</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultationDetail.observations || 'Aucune observation'}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Traitement</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultationDetail.traitement || 'Aucun traitement'}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Bilan</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultationDetail.bilan || 'Aucun bilan'}
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowConsultationDetailModal(false);
                    editConsultation(selectedConsultationDetail);
                  }}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                >
                  <Edit className="w-4 h-4" />
                  <span>Modifier</span>
                </button>
                <button
                  onClick={() => setShowConsultationDetailModal(false)}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Consultation Modal */}
      {showEditConsultationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Modifier la consultation
                </h2>
                <button
                  onClick={() => setShowEditConsultationModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Observations */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observations cliniques
                  </label>
                  <textarea
                    value={consultationFormData.observations}
                    onChange={(e) => setConsultationFormData({...consultationFormData, observations: e.target.value})}
                    className="input-field"
                    rows="4"
                    placeholder="Observations et examens cliniques..."
                  />
                </div>

                {/* Traitement */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Traitement prescrit
                  </label>
                  <textarea
                    value={consultationFormData.traitement}
                    onChange={(e) => setConsultationFormData({...consultationFormData, traitement: e.target.value})}
                    className="input-field"
                    rows="3"
                    placeholder="Médicaments et posologie..."
                  />
                </div>

                {/* Bilan */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bilan/Examens
                  </label>
                  <textarea
                    value={consultationFormData.bilan}
                    onChange={(e) => setConsultationFormData({...consultationFormData, bilan: e.target.value})}
                    className="input-field"
                    rows="3"
                    placeholder="Examens complémentaires demandés..."
                  />
                </div>

                {/* Relance */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date de relance
                  </label>
                  <input
                    type="date"
                    value={consultationFormData.relance_date}
                    onChange={(e) => setConsultationFormData({...consultationFormData, relance_date: e.target.value})}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowEditConsultationModal(false)}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  onClick={saveConsultation}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                >
                  <Save className="w-4 h-4" />
                  <span>Sauvegarder</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Consultation;