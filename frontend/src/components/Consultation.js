import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search,
  User,
  Phone,
  MapPin,
  UserCheck,
  Calendar,
  Plus,
  Eye,
  Edit,
  Trash2,
  MessageCircle,
  Clock,
  Weight,
  Ruler,
  Brain,
  FileText,
  Save,
  Play,
  Pause,
  Square,
  Minimize2,
  Maximize2,
  X
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Consultation = ({ user }) => {
  // États principaux
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredPatients, setFilteredPatients] = useState([]);
  
  // États du modal consultation
  const [consultationModal, setConsultationModal] = useState({
    isOpen: false,
    isMinimized: false,
    mode: 'create', // 'create', 'view', 'edit'
    consultationId: null
  });
  
  // États du modal de visualisation
  const [viewModal, setViewModal] = useState({
    isOpen: false,
    consultation: null
  });
  
  // Chronomètre
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  
  // Données de la consultation
  const [consultationData, setConsultationData] = useState({
    patient_id: '',
    date: new Date().toISOString().split('T')[0],
    type_rdv: 'visite', // Par défaut une visite
    poids: '',
    taille: '',
    pc: '',
    observation_medicale: '',
    traitement: '',
    bilans: '',
    relance_telephonique: false,
    date_relance: '',
    duree: 0
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Chargement initial des patients
  useEffect(() => {
    fetchPatients();
  }, []);

  // Gestion du chronomètre
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

  // Filtrage des patients
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredPatients([]);
    } else {
      const filtered = patients.filter(patient =>
        `${patient.prenom} ${patient.nom}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.telephone?.includes(searchTerm)
      );
      setFilteredPatients(filtered.slice(0, 10)); // Limite à 10 résultats
    }
  }, [searchTerm, patients]);

  // Charger tous les patients
  const fetchPatients = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(response.data.patients || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
      toast.error('Erreur lors du chargement des patients');
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL]);

  // Charger les consultations d'un patient
  const fetchPatientConsultations = useCallback(async (patientId) => {
    try {
      // Force fresh data by adding timestamp to prevent caching
      const timestamp = Date.now();
      const response = await axios.get(`${API_BASE_URL}/api/consultations/patient/${patientId}?_t=${timestamp}`);
      setConsultations(response.data || []);
    } catch (error) {
      console.error('Error fetching consultations:', error);
      toast.error('Erreur lors du chargement des consultations');
    }
  }, [API_BASE_URL]);

  // Sélectionner un patient
  const handlePatientSelect = useCallback(async (patient) => {
    setSelectedPatient(patient);
    setSearchTerm(`${patient.prenom} ${patient.nom}`);
    setFilteredPatients([]);
    await fetchPatientConsultations(patient.id);
  }, [fetchPatientConsultations]);

  // Actualiser les consultations
  const refreshConsultations = useCallback(async () => {
    if (selectedPatient) {
      await fetchPatientConsultations(selectedPatient.id);
    }
  }, [selectedPatient, fetchPatientConsultations]);

  // Ouvrir modal d'ajout de consultation
  const handleAddConsultation = () => {
    if (!selectedPatient) {
      toast.error('Veuillez sélectionner un patient');
      return;
    }

    setConsultationData({
      patient_id: selectedPatient.id,
      date: new Date().toISOString().split('T')[0],
      type_rdv: 'visite', // Par défaut une visite
      poids: '',
      taille: '',
      pc: '',
      observation_medicale: '',
      traitement: '',
      bilans: '',
      relance_telephonique: false,
      date_relance: '',
      duree: 0
    });

    setConsultationModal({
      isOpen: true,
      isMinimized: false,
      mode: 'create',
      consultationId: null
    });

    // Démarrer le chronomètre
    setTimer(0);
    setIsRunning(true);
  };

  // Obtenir le montant payé pour une consultation
  const getPaymentAmount = useCallback(async (appointmentId) => {
    try {
      // Add cache-busting parameter and headers to ensure fresh data
      const timestamp = Date.now();
      const response = await axios.get(`${API_BASE_URL}/api/payments?_t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      const payments = response.data || [];
      
      // Find payment with matching appointment_id and statut='paye'
      const payment = payments.find(p => 
        p.appointment_id === appointmentId && p.statut === 'paye'
      );
      
      return payment ? payment.montant : null;
    } catch (error) {
      console.error('Error fetching payment amount:', error);
      return null;
    }
  }, [API_BASE_URL]);

  // Voir une consultation avec montant
  const handleViewConsultation = async (consultation) => {
    let paymentAmount = null;
    
    // Attendre la récupération du montant de paiement pour les visites
    if (consultation.type_rdv === 'visite') {
      paymentAmount = await getPaymentAmount(consultation.appointment_id);
    }
    
    // Ouvrir le modal seulement après avoir récupéré les données de paiement
    setViewModal({
      isOpen: true,
      consultation: { ...consultation, paymentAmount }
    });
  };

  // Modifier une consultation
  const handleEditConsultation = (consultation) => {
    setConsultationData({
      patient_id: consultation.patient_id,
      date: consultation.date,
      type_rdv: consultation.type_rdv || 'visite',
      poids: consultation.poids || '',
      taille: consultation.taille || '',
      pc: consultation.pc || '',
      observation_medicale: consultation.observations || '',
      traitement: consultation.traitement || '',
      bilans: consultation.bilan || '',
      relance_telephonique: consultation.relance_date ? true : false,
      date_relance: consultation.relance_date || '',
      duree: consultation.duree || 0
    });

    setConsultationModal({
      isOpen: true,
      isMinimized: false,
      mode: 'edit',
      consultationId: consultation.id
    });

    setTimer(consultation.duree * 60 || 0); // Convertir minutes en secondes
    setIsRunning(false);
  };

  // Supprimer une consultation
  const handleDeleteConsultation = async (consultationId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette consultation ?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/api/consultations/${consultationId}`);
      toast.success('Consultation supprimée avec succès');
      if (selectedPatient) {
        await fetchPatientConsultations(selectedPatient.id);
      }
    } catch (error) {
      console.error('Error deleting consultation:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  // Fermer le modal de consultation
  const fermerModalConsultation = () => {
    setConsultationModal({
      isOpen: false,
      isMinimized: false,
      mode: 'create',
      consultationId: null
    });
    setIsRunning(false);
    setTimer(0);
  };

  // Réduire le modal
  const reduireModalConsultation = () => {
    setConsultationModal(prev => ({
      ...prev,
      isMinimized: true
    }));
  };

  // Restaurer le modal
  const restaurerModalConsultation = () => {
    setConsultationModal(prev => ({
      ...prev,
      isMinimized: false
    }));
  };

  // Sauvegarder la consultation
  const sauvegarderConsultation = async () => {
    try {
      setIsRunning(false);
      
      const consultationPayload = {
        patient_id: consultationData.patient_id,
        appointment_id: consultationData.appointment_id || `consultation_${Date.now()}`, // Generate ID if not from appointment
        date: consultationData.date,
        type_rdv: consultationData.type_rdv,
        duree: Math.floor(timer / 60), // Convertir en minutes
        poids: parseFloat(consultationData.poids) || 0,
        taille: parseFloat(consultationData.taille) || 0,
        pc: parseFloat(consultationData.pc) || 0,
        observations: consultationData.observation_medicale,
        traitement: consultationData.traitement,
        bilan: consultationData.bilans,
        relance_date: consultationData.relance_telephonique ? consultationData.date_relance : ""
      };

      if (consultationModal.mode === 'create') {
        await axios.post(`${API_BASE_URL}/api/consultations`, consultationPayload);
        toast.success('Consultation créée avec succès');
      } else if (consultationModal.mode === 'edit') {
        await axios.put(`${API_BASE_URL}/api/consultations/${consultationModal.consultationId}`, consultationPayload);
        toast.success('Consultation modifiée avec succès');
      }

      fermerModalConsultation();
      if (selectedPatient) {
        await fetchPatientConsultations(selectedPatient.id);
      }
    } catch (error) {
      console.error('Error saving consultation:', error);
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  // Formater le temps
  const formatTimer = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Obtenir le lien WhatsApp
  const getWhatsAppLink = (numero) => {
    if (!numero) return '#';
    const cleanNumber = numero.replace(/\D/g, '');
    return `https://wa.me/212${cleanNumber.startsWith('0') ? cleanNumber.substring(1) : cleanNumber}`;
  };

  // Formater la date
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Calculer l'âge
  const calculateAge = (dateOfBirth) => {
    if (!dateOfBirth) return 'N/A';
    const today = new Date();
    const birth = new Date(dateOfBirth);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Consultations</h1>
          <p className="text-gray-600">Gestion des consultations par patient</p>
        </div>
        <button
          onClick={handleAddConsultation}
          disabled={!selectedPatient}
          className={`btn-primary flex items-center space-x-2 ${
            !selectedPatient ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <Plus className="w-5 h-5" />
          <span>Ajouter Consultation</span>
        </button>
      </div>

      {/* Champ de recherche patient */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un patient (nom, prénom, téléphone)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 input-field w-full"
          />
        </div>
        
        {/* Dropdown des résultats */}
        {filteredPatients.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
            {filteredPatients.map((patient) => (
              <button
                key={patient.id}
                onClick={() => handlePatientSelect(patient)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-gray-900">
                  {patient.prenom} {patient.nom}
                </div>
                <div className="text-sm text-gray-600">
                  {patient.telephone} • {calculateAge(patient.date_naissance)} ans
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedPatient && (
        <>
          {/* Bannière patient sélectionné */}
          <div className="bg-primary-50 border border-primary-200 rounded-xl p-6">
            <div className="flex items-center space-x-4">
              <div className="bg-primary-100 p-3 rounded-full">
                <User className="w-8 h-8 text-primary-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-primary-900">
                  {selectedPatient.prenom} {selectedPatient.nom}
                </h2>
                <p className="text-primary-700">
                  {calculateAge(selectedPatient.date_naissance)} ans • {consultations.length} consultation{consultations.length > 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Colonne gauche - Détails du patient */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations Patient</h3>
                
                <div className="space-y-4">
                  {/* Informations personnelles */}
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <User className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Âge</span>
                    </div>
                    <p className="text-gray-900 ml-6">{calculateAge(selectedPatient.date_naissance)} ans</p>
                  </div>

                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Calendar className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Date de naissance</span>
                    </div>
                    <p className="text-gray-900 ml-6">{selectedPatient.date_naissance ? formatDate(selectedPatient.date_naissance) : 'N/A'}</p>
                  </div>

                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <MapPin className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Adresse</span>
                    </div>
                    <p className="text-gray-900 ml-6">{selectedPatient.adresse || 'Non renseignée'}</p>
                  </div>

                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Phone className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Téléphone</span>
                    </div>
                    <div className="flex items-center space-x-2 ml-6">
                      <span className="text-gray-900">{selectedPatient.telephone}</span>
                      {selectedPatient.numero_whatsapp && (
                        <a
                          href={getWhatsAppLink(selectedPatient.numero_whatsapp)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Informations des parents */}
                  {(selectedPatient.pere || selectedPatient.mere) && (
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-3">Parents</h4>
                      
                      {selectedPatient.pere && (
                        <div className="mb-3">
                          <div className="flex items-center space-x-2 mb-1">
                            <UserCheck className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Père</span>
                          </div>
                          <div className="ml-6 space-y-1">
                            <p className="text-gray-900">{selectedPatient.pere.nom}</p>
                            <p className="text-sm text-gray-600">{selectedPatient.pere.fonction}</p>
                            <p className="text-sm text-gray-600">{selectedPatient.pere.telephone}</p>
                          </div>
                        </div>
                      )}

                      {selectedPatient.mere && (
                        <div>
                          <div className="flex items-center space-x-2 mb-1">
                            <UserCheck className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Mère</span>
                          </div>
                          <div className="ml-6 space-y-1">
                            <p className="text-gray-900">{selectedPatient.mere.nom}</p>
                            <p className="text-sm text-gray-600">{selectedPatient.mere.fonction}</p>
                            <p className="text-sm text-gray-600">{selectedPatient.mere.telephone}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Antécédents */}
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Antécédents</span>
                    </div>
                    <p className="text-gray-900 ml-6 text-sm">{selectedPatient.antecedents || 'Aucun antécédent'}</p>
                  </div>

                  {/* Notes */}
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Notes</span>
                    </div>
                    <p className="text-gray-900 ml-6 text-sm">{selectedPatient.notes || 'Aucune note'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Partie centrale - Historique des consultations */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Historique des Consultations ({consultations.length})
                  </h3>
                  <button
                    onClick={refreshConsultations}
                    className="flex items-center space-x-2 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Actualiser les consultations"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Actualiser</span>
                  </button>
                </div>

                <div className="p-6">
                  {consultations.length === 0 ? (
                    <div className="text-center py-12">
                      <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h4 className="text-lg font-medium text-gray-900 mb-2">Aucune consultation</h4>
                      <p className="text-gray-600 mb-6">Ce patient n'a pas encore de consultations enregistrées</p>
                      <button
                        onClick={handleAddConsultation}
                        className="btn-primary inline-flex items-center space-x-2"
                      >
                        <Plus className="w-5 h-5" />
                        <span>Première consultation</span>
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {consultations
                        .sort((a, b) => new Date(b.date) - new Date(a.date))
                        .map((consultation) => (
                          <div
                            key={consultation.id}
                            className={`border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow ${
                              consultation.type_rdv === 'controle' ? 'ml-6' : ''
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-4">
                                {/* Badge type consultation avec nouveaux codes couleur */}
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                  consultation.type_rdv === 'visite'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-green-100 text-green-800'
                                }`}>
                                  {consultation.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                                </span>
                                
                                <div>
                                  <div className="flex items-center space-x-2">
                                    <Calendar className="w-4 h-4 text-gray-500" />
                                    <span className="font-medium text-gray-900">
                                      {formatDate(consultation.date)}
                                    </span>
                                    {consultation.duree && (
                                      <>
                                        <Clock className="w-4 h-4 text-gray-500 ml-4" />
                                        <span className="text-gray-600">{consultation.duree} min</span>
                                      </>
                                    )}
                                  </div>
                                  {consultation.observations && (
                                    <p className="text-gray-600 text-sm mt-1 line-clamp-2">
                                      {consultation.observations}
                                    </p>
                                  )}
                                </div>
                              </div>

                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => handleViewConsultation(consultation)}
                                  className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                                  title="Voir"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleEditConsultation(consultation)}
                                  className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                                  title="Modifier"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDeleteConsultation(consultation.id)}
                                  className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                                  title="Supprimer"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Modal de visualisation des consultations */}
      {viewModal.isOpen && viewModal.consultation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    Consultation du {formatDate(viewModal.consultation.date)}
                  </h2>
                  <p className="text-gray-600">
                    {selectedPatient?.prenom} {selectedPatient?.nom}
                  </p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      viewModal.consultation.type_rdv === 'visite'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {viewModal.consultation.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                    </span>
                    {viewModal.consultation.type_rdv === 'visite' && viewModal.consultation.paymentAmount && (
                      <span className="text-gray-600">
                        ({viewModal.consultation.paymentAmount} DH)
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setViewModal({ isOpen: false, consultation: null })}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Mesures */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Poids :</span>
                      <span className="font-medium">{viewModal.consultation.poids || 'N/A'} kg</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Taille :</span>
                      <span className="font-medium">{viewModal.consultation.taille || 'N/A'} cm</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">PC :</span>
                      <span className="font-medium">{viewModal.consultation.pc || 'N/A'} cm</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Durée :</span>
                      <span className="font-medium">{viewModal.consultation.duree || 'N/A'} min</span>
                    </div>
                  </div>
                </div>

                {/* Informations consultation */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Type & Date</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Type :</span>
                      <div className="flex items-center space-x-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          viewModal.consultation.type_rdv === 'visite'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {viewModal.consultation.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                        </span>
                        {viewModal.consultation.type_rdv === 'visite' && viewModal.consultation.paymentAmount != null && (
                          <span className="text-gray-600 text-sm">
                            ({viewModal.consultation.paymentAmount} DH)
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Date :</span>
                      <span className="font-medium">{formatDate(viewModal.consultation.date)}</span>
                    </div>
                    {viewModal.consultation.relance_date && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Relance :</span>
                        <span className="font-medium">{formatDate(viewModal.consultation.relance_date)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Observations et traitement */}
              <div className="mt-6 space-y-6">
                {viewModal.consultation.observations && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Observations médicales</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-900 whitespace-pre-wrap">{viewModal.consultation.observations}</p>
                    </div>
                  </div>
                )}

                {viewModal.consultation.traitement && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Traitement</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-900 whitespace-pre-wrap">{viewModal.consultation.traitement}</p>
                    </div>
                  </div>
                )}

                {viewModal.consultation.bilan && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Bilans</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-900 whitespace-pre-wrap">{viewModal.consultation.bilan}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setViewModal({ isOpen: false, consultation: null })}
                  className="btn-outline"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de consultation (création/modification) */}
      {consultationModal.isOpen && (
        <>
          {/* Modal réduit */}
          {consultationModal.isMinimized ? (
            <div className="fixed bottom-4 right-4 z-50">
              <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[300px]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-gray-900">
                      {selectedPatient?.prenom} {selectedPatient?.nom}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-mono text-blue-600">
                      {formatTimer(timer)}
                    </span>
                    <button
                      onClick={restaurerModalConsultation}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <Maximize2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Modal complet */
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  {/* Header du modal */}
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        {consultationModal.mode === 'create' ? 'Nouvelle Consultation' : 'Modifier Consultation'} - {selectedPatient?.prenom} {selectedPatient?.nom}
                      </h2>
                      <p className="text-gray-600">
                        {formatDate(consultationData.date)} - {formatTimer(timer)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={reduireModalConsultation}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                      >
                        <Minimize2 className="w-5 h-5" />
                      </button>
                      <button
                        onClick={fermerModalConsultation}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Chronomètre */}
                  <div className="bg-blue-50 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Clock className="w-6 h-6 text-blue-600" />
                        <span className="text-lg font-semibold text-blue-900">
                          Durée: {formatTimer(timer)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setIsRunning(!isRunning)}
                          className={`p-2 rounded-lg ${
                            isRunning 
                              ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                              : 'bg-green-100 text-green-600 hover:bg-green-200'
                          }`}
                        >
                          {isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                        </button>
                        <button
                          onClick={() => {
                            setIsRunning(false);
                            setTimer(0);
                          }}
                          className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg"
                        >
                          <Square className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Formulaire de consultation */}
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    sauvegarderConsultation();
                  }}>
                    <div className="space-y-6">
                      {/* Date et type de consultation */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Date de consultation
                          </label>
                          <input
                            type="date"
                            value={consultationData.date}
                            onChange={(e) => setConsultationData({...consultationData, date: e.target.value})}
                            className="input-field"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Type de consultation
                          </label>
                          <select
                            value={consultationData.type_rdv}
                            onChange={(e) => setConsultationData({...consultationData, type_rdv: e.target.value})}
                            className="input-field"
                          >
                            <option value="visite">Visite</option>
                            <option value="controle">Contrôle</option>
                          </select>
                        </div>
                      </div>

                      {/* Mesures */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              <Weight className="w-4 h-4 inline mr-1" />
                              Poids (kg)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={consultationData.poids}
                              onChange={(e) => setConsultationData({...consultationData, poids: e.target.value})}
                              className="input-field"
                              placeholder="0.0"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              <Ruler className="w-4 h-4 inline mr-1" />
                              Taille (cm)
                            </label>
                            <input
                              type="number"
                              value={consultationData.taille}
                              onChange={(e) => setConsultationData({...consultationData, taille: e.target.value})}
                              className="input-field"
                              placeholder="0"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              <Brain className="w-4 h-4 inline mr-1" />
                              PC (cm)
                            </label>
                            <input
                              type="number"
                              value={consultationData.pc}
                              onChange={(e) => setConsultationData({...consultationData, pc: e.target.value})}
                              className="input-field"
                              placeholder="0"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Observations et traitement */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Observation médicale
                          </label>
                          <textarea
                            value={consultationData.observation_medicale}
                            onChange={(e) => setConsultationData({...consultationData, observation_medicale: e.target.value})}
                            className="input-field"
                            rows="4"
                            placeholder="Observations du médecin..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Traitement
                          </label>
                          <textarea
                            value={consultationData.traitement}
                            onChange={(e) => setConsultationData({...consultationData, traitement: e.target.value})}
                            className="input-field"
                            rows="4"
                            placeholder="Traitement prescrit..."
                          />
                        </div>
                      </div>

                      {/* Bilans */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Bilans
                        </label>
                        <textarea
                          value={consultationData.bilans}
                          onChange={(e) => setConsultationData({...consultationData, bilans: e.target.value})}
                          className="input-field"
                          rows="3"
                          placeholder="Bilans demandés..."
                        />
                      </div>

                      {/* Relance téléphonique */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Relance téléphonique</h3>
                        <div className="flex items-center space-x-4">
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={consultationData.relance_telephonique}
                              onChange={(e) => setConsultationData({...consultationData, relance_telephonique: e.target.checked})}
                              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                              <Phone className="w-4 h-4 inline mr-1" />
                              Programmer une relance
                            </span>
                          </label>
                          {consultationData.relance_telephonique && (
                            <div>
                              <input
                                type="date"
                                value={consultationData.date_relance}
                                onChange={(e) => setConsultationData({...consultationData, date_relance: e.target.value})}
                                className="input-field"
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Boutons */}
                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        type="button"
                        onClick={fermerModalConsultation}
                        className="btn-outline"
                      >
                        Annuler
                      </button>
                      <button
                        type="submit"
                        className="btn-primary flex items-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>{consultationModal.mode === 'create' ? 'Sauvegarder' : 'Modifier'}</span>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Consultation;