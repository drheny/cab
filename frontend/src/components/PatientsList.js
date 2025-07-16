import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Phone, 
  Calendar, 
  User,
  MessageCircle,
  ChevronLeft,
  ChevronRight,
  Eye,
  MapPin,
  Clock,
  Users,
  FileText,
  Save,
  X,
  Weight,
  Ruler,
  Brain,
  Stethoscope,
  CalendarPlus
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const PatientsListComponent = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [consultationDetails, setConsultationDetails] = useState([]);
  const [loadingConsultations, setLoadingConsultations] = useState(false);
  const [showConsultationDetailsModal, setShowConsultationDetailsModal] = useState(false);
  const [showEditConsultationModal, setShowEditConsultationModal] = useState(false);
  const [showAddConsultationModal, setShowAddConsultationModal] = useState(false);
  const [editingConsultation, setEditingConsultation] = useState(null);
  const [consultationFormData, setConsultationFormData] = useState({
    poids: '',
    taille: '',
    pc: '',
    observations: '',
    traitement: '',
    bilan: '',
    relance_date: '',
    duree: ''
  });
  const searchInputRef = useRef(null);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    date_naissance: '',
    adresse: '',
    pere: {
      nom: '',
      telephone: '',
      fonction: ''
    },
    mere: {
      nom: '',
      telephone: '',
      fonction: ''
    },
    numero_whatsapp: '',
    notes: '',
    antecedents: '',
    // Anciens champs pour compatibilité
    sexe: 'M',
    telephone: '',
    nom_parent: '',
    telephone_parent: '',
    assurance: '',
    numero_assurance: '',
    allergies: ''
  });

  // Optimized fetchPatients with separated loading states
  const fetchPatients = useCallback(async (isSearch = false) => {
    try {
      // Use different loading state for search vs initial load
      if (isSearch) {
        setSearchLoading(true);
      } else {
        setLoading(true);
      }
      
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients`, {
        params: {
          page: currentPage,
          limit: 10,
          search: debouncedSearchTerm
        }
      });
      setPatients(response.data.patients);
      setTotalCount(response.data.total_count);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Error fetching patients:', error);
      toast.error('Erreur lors du chargement des patients');
    } finally {
      if (isSearch) {
        setSearchLoading(false);
      } else {
        setLoading(false);
      }
    }
  }, [currentPage, debouncedSearchTerm]);

  // Initial load only
  useEffect(() => {
    fetchPatients(false);
    
    // Vérifier si on doit ouvrir le modal d'ajout automatiquement
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('action') === 'add') {
      openModal();
      // Nettoyer l'URL
      window.history.replaceState({}, '', '/patients');
    }
  }, [location]);

  // Page change effect
  useEffect(() => {
    if (currentPage > 1 || debouncedSearchTerm) {
      fetchPatients(true); // Use search loading for pagination/search
    }
  }, [currentPage, debouncedSearchTerm, fetchPatients]);

  // Debounce search term - no loading state change here
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setCurrentPage(1);
    }, 250); // Even faster debounce

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Format date function
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  // Handle search with completely isolated state management
  const handleSearch = useCallback((e) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Immediate visual feedback without triggering re-render
    e.target.value = value;
  }, []);

  // Prevent any re-render during typing
  const searchInputProps = useMemo(() => ({
    ref: searchInputRef,
    type: "text",
    placeholder: "Rechercher par nom, prénom ou date de naissance...",
    defaultValue: searchTerm,
    onChange: handleSearch,
    className: "w-full pl-8 sm:pl-10 pr-4 py-2 sm:py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 responsive-text",
    key: "search-input" // Ensure stable key
  }), [handleSearch, searchTerm]);

  const handleCreatePatient = async () => {
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/patients`, formData);
      toast.success('Patient créé avec succès');
      setShowModal(false);
      resetForm();
      fetchPatients();
    } catch (error) {
      console.error('Error creating patient:', error);
      toast.error('Erreur lors de la création du patient');
    }
  };

  const handleUpdatePatient = async () => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${selectedPatient.id}`, formData);
      toast.success('Patient mis à jour avec succès');
      setShowModal(false);
      resetForm();
      fetchPatients();
    } catch (error) {
      console.error('Error updating patient:', error);
      toast.error('Erreur lors de la mise à jour du patient');
    }
  };

  const handleDeletePatient = async (patientId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce patient ?')) {
      try {
        await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}`);
        toast.success('Patient supprimé avec succès');
        fetchPatients();
      } catch (error) {
        console.error('Error deleting patient:', error);
        toast.error('Erreur lors de la suppression du patient');
      }
    }
  };

  const viewPatientDetails = async (patientId) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}`);
      setSelectedPatient(response.data);
      setShowPatientModal(true);
      
      // Load consultations data without opening the overlay
      loadConsultationsData(patientId);
    } catch (error) {
      console.error('Error fetching patient details:', error);
      toast.error('Erreur lors du chargement des détails du patient');
    }
  };

  const loadConsultationsData = async (patientId) => {
    try {
      setLoadingConsultations(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}/consultations`);
      setConsultationDetails(response.data);
    } catch (error) {
      console.error('Error fetching consultation details:', error);
      toast.error('Erreur lors du chargement des détails des consultations');
    } finally {
      setLoadingConsultations(false);
    }
  };

  const viewConsultationDetails = async (patientId) => {
    try {
      setLoadingConsultations(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}/consultations`);
      setConsultationDetails(response.data);
      setShowConsultationModal(true);
    } catch (error) {
      console.error('Error fetching consultation details:', error);
      toast.error('Erreur lors du chargement des détails des consultations');
    } finally {
      setLoadingConsultations(false);
    }
  };

  const viewSingleConsultation = async (consultationId) => {
    try {
      const consultation = consultationDetails.find(c => c.id === consultationId);
      if (consultation) {
        setSelectedConsultation(consultation);
        setShowConsultationDetailsModal(true);
      }
    } catch (error) {
      console.error('Error viewing consultation:', error);
      toast.error('Erreur lors de l\'affichage de la consultation');
    }
  };

  const editConsultation = (consultation) => {
    setEditingConsultation(consultation);
    setConsultationFormData({
      poids: consultation.poids?.toString() || '',
      taille: consultation.taille?.toString() || '',
      pc: consultation.pc?.toString() || '',
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
      
      const updatedConsultation = {
        ...editingConsultation,
        poids: parseFloat(consultationFormData.poids) || 0,
        taille: parseFloat(consultationFormData.taille) || 0,
        pc: parseFloat(consultationFormData.pc) || 0,
        observations: consultationFormData.observations,
        traitement: consultationFormData.traitement,
        bilan: consultationFormData.bilan,
        relance_date: consultationFormData.relance_date,
        duree: parseInt(consultationFormData.duree) || 0
      };

      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/consultations/${editingConsultation.id}`, updatedConsultation);
      
      toast.success('Consultation mise à jour avec succès');
      setShowEditConsultationModal(false);
      setEditingConsultation(null);
      
      // Refresh consultations data
      if (selectedPatient) {
        loadConsultationsData(selectedPatient.id);
      }
    } catch (error) {
      console.error('Error saving consultation:', error);
      toast.error('Erreur lors de la sauvegarde de la consultation');
    }
  };

  const deleteConsultation = async (consultationId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette consultation ?')) {
      try {
        await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/api/consultations/${consultationId}`);
        toast.success('Consultation supprimée avec succès');
        
        // Refresh consultations data
        if (selectedPatient) {
          loadConsultationsData(selectedPatient.id);
        }
      } catch (error) {
        console.error('Error deleting consultation:', error);
        toast.error('Erreur lors de la suppression de la consultation');
      }
    }
  };

  const addNewConsultation = () => {
    setConsultationFormData({
      poids: '',
      taille: '',
      pc: '',
      observations: '',
      traitement: '',
      bilan: '',
      relance_date: '',
      duree: ''
    });
    setShowAddConsultationModal(true);
  };

  const createConsultation = async () => {
    try {
      if (!selectedPatient) return;
      
      const newConsultation = {
        patient_id: selectedPatient.id,
        appointment_id: 'manual_' + Date.now(),
        date: new Date().toISOString().split('T')[0],
        poids: parseFloat(consultationFormData.poids) || 0,
        taille: parseFloat(consultationFormData.taille) || 0,
        pc: parseFloat(consultationFormData.pc) || 0,
        observations: consultationFormData.observations,
        traitement: consultationFormData.traitement,
        bilan: consultationFormData.bilan,
        relance_date: consultationFormData.relance_date,
        duree: parseInt(consultationFormData.duree) || 0
      };

      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/consultations`, newConsultation);
      
      toast.success('Consultation créée avec succès');
      setShowAddConsultationModal(false);
      
      // Refresh consultations data
      loadConsultationsData(selectedPatient.id);
    } catch (error) {
      console.error('Error creating consultation:', error);
      toast.error('Erreur lors de la création de la consultation');
    }
  };

  const addNewAppointment = () => {
    // Navigate to calendar with patient pre-selected
    navigate('/calendar', { state: { selectedPatient: selectedPatient } });
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

  const resetForm = () => {
    setFormData({
      nom: '',
      prenom: '',
      date_naissance: '',
      adresse: '',
      pere: {
        nom: '',
        telephone: '',
        fonction: ''
      },
      mere: {
        nom: '',
        telephone: '',
        fonction: ''
      },
      numero_whatsapp: '',
      notes: '',
      antecedents: '',
      sexe: 'M',
      telephone: '',
      nom_parent: '',
      telephone_parent: '',
      assurance: '',
      numero_assurance: '',
      allergies: ''
    });
    setSelectedPatient(null);
  };

  const openModal = (patient = null) => {
    if (patient) {
      setSelectedPatient(patient);
      setFormData({
        ...patient,
        pere: patient.pere || { nom: '', telephone: '', fonction: '' },
        mere: patient.mere || { nom: '', telephone: '', fonction: '' }
      });
    } else {
      resetForm();
    }
    setShowModal(true);
  };

  // Memoize the patients list rendering to prevent unnecessary re-renders
  const patientsListContent = useMemo(() => {
    return patients.map((patient) => (
      <div key={patient.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
        {/* Desktop Layout */}
        <div className="hidden md:block p-4">
          <div className="grid grid-cols-12 gap-4 items-center">
            <div className="col-span-2">
              <button
                onClick={() => viewPatientDetails(patient.id)}
                className="text-left hover:text-primary-600 transition-colors"
              >
                <div className="font-semibold text-gray-900">
                  {patient.prenom} {patient.nom}
                </div>
              </button>
            </div>
            <div className="col-span-2">
              <span className="text-sm text-gray-600">
                {formatDate(patient.date_naissance)}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-sm text-gray-600">
                {patient.mere?.nom || 'N/A'}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-sm text-gray-600">
                {patient.mere?.telephone || 'N/A'}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-sm text-gray-600 truncate block">
                {patient.adresse || 'N/A'}
              </span>
            </div>
            <div className="col-span-1">
              {patient.lien_whatsapp ? (
                <a
                  href={patient.lien_whatsapp}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 bg-green-500 hover:bg-green-600 text-white text-sm px-3 py-1 rounded-lg transition-colors"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>WA</span>
                </a>
              ) : (
                <span className="text-sm text-gray-400">N/A</span>
              )}
            </div>
            <div className="col-span-1">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => openModal(patient)}
                  className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeletePatient(patient.id)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Layout */}
        <div className="md:hidden p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <button
                onClick={() => viewPatientDetails(patient.id)}
                className="text-left hover:text-primary-600 transition-colors"
              >
                <h3 className="font-semibold text-gray-900">
                  {patient.prenom} {patient.nom}
                </h3>
              </button>
              <p className="text-sm text-gray-500">
                {formatDate(patient.date_naissance)}
              </p>
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => openModal(patient)}
                className="p-1.5 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
              >
                <Edit className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDeletePatient(patient.id)}
                className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="space-y-2 mb-3">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <User className="w-4 h-4 text-gray-400" />
              <span>Mère: {patient.mere?.nom || 'N/A'}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Phone className="w-4 h-4 text-gray-400" />
              <span>Tel mère: {patient.mere?.telephone || 'N/A'}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="truncate">{patient.adresse || 'N/A'}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {patient.lien_whatsapp ? (
              <a
                href={patient.lien_whatsapp}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded-lg flex items-center justify-center space-x-1 transition-colors"
              >
                <MessageCircle className="w-4 h-4" />
                <span>WhatsApp</span>
              </a>
            ) : (
              <div className="flex-1 bg-gray-200 text-gray-500 text-sm py-2 px-3 rounded-lg flex items-center justify-center">
                <span>Pas de WhatsApp</span>
              </div>
            )}
          </div>
        </div>
      </div>
    ));
  }, [patients]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header avec compteur */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="responsive-title font-bold text-gray-900">Patients</h1>
            <span className="bg-primary-100 text-primary-800 text-sm font-medium px-3 py-1 rounded-full">
              Total: {totalCount}
            </span>
          </div>
          <p className="text-gray-600 responsive-text">Gestion des fiches patients</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center justify-center space-x-2 responsive-button"
        >
          <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
          <span>Nouveau Patient</span>
        </button>
      </div>

      {/* Search with isolated rendering */}
      <div className="relative mb-4 sm:mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 sm:w-5 sm:h-5" />
        <input {...searchInputProps} />
        {searchLoading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
          </div>
        )}
      </div>

      {/* Table Header (Hidden on mobile) */}
      <div className="hidden md:block">
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-600">
            <div className="col-span-2">Nom Prénom</div>
            <div className="col-span-2">Date naissance</div>
            <div className="col-span-2">Nom mère</div>
            <div className="col-span-2">Tel mère</div>
            <div className="col-span-2">Adresse</div>
            <div className="col-span-1">WhatsApp</div>
            <div className="col-span-1">Actions</div>
          </div>
        </div>
      </div>

      {/* Patients List - Using memoized content */}
      <div className="space-y-3">
        {patientsListContent}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-700">
            Affichage {((currentPage - 1) * 10) + 1} à {Math.min(currentPage * 10, totalCount)} sur {totalCount} patients
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center space-x-1">
              {[...Array(totalPages)].map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentPage(index + 1)}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    currentPage === index + 1
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Add/Edit Patient Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                {selectedPatient ? 'Modifier le patient' : 'Nouveau patient'}
              </h2>

              <form onSubmit={(e) => {
                e.preventDefault();
                selectedPatient ? handleUpdatePatient() : handleCreatePatient();
              }}>
                <div className="space-y-6">
                  {/* Informations personnelles */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations personnelles</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                        <input
                          type="text"
                          value={formData.nom}
                          onChange={(e) => setFormData({...formData, nom: e.target.value})}
                          className="input-field"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Prénom *</label>
                        <input
                          type="text"
                          value={formData.prenom}
                          onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                          className="input-field"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Date de naissance</label>
                        <input
                          type="date"
                          value={formData.date_naissance}
                          onChange={(e) => setFormData({...formData, date_naissance: e.target.value})}
                          className="input-field"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
                        <input
                          type="text"
                          value={formData.adresse}
                          onChange={(e) => setFormData({...formData, adresse: e.target.value})}
                          className="input-field"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Informations des parents */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations des parents</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-md font-medium text-gray-800 mb-3">Père</h4>
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                            <input
                              type="text"
                              value={formData.pere.nom}
                              onChange={(e) => setFormData({...formData, pere: {...formData.pere, nom: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                            <input
                              type="tel"
                              value={formData.pere.telephone}
                              onChange={(e) => setFormData({...formData, pere: {...formData.pere, telephone: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Fonction</label>
                            <input
                              type="text"
                              value={formData.pere.fonction}
                              onChange={(e) => setFormData({...formData, pere: {...formData.pere, fonction: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-md font-medium text-gray-800 mb-3">Mère</h4>
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                            <input
                              type="text"
                              value={formData.mere.nom}
                              onChange={(e) => setFormData({...formData, mere: {...formData.mere, nom: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                            <input
                              type="tel"
                              value={formData.mere.telephone}
                              onChange={(e) => setFormData({...formData, mere: {...formData.mere, telephone: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Fonction</label>
                            <input
                              type="text"
                              value={formData.mere.fonction}
                              onChange={(e) => setFormData({...formData, mere: {...formData.mere, fonction: e.target.value}})}
                              className="input-field"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Contact et médical */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact et informations médicales</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Numéro WhatsApp
                          <span className="text-sm text-gray-500 ml-1">(216xxxxxxxx)</span>
                        </label>
                        <input
                          type="tel"
                          value={formData.numero_whatsapp}
                          onChange={(e) => setFormData({...formData, numero_whatsapp: e.target.value})}
                          className="input-field"
                          placeholder="216xxxxxxxx"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sexe</label>
                        <select
                          value={formData.sexe}
                          onChange={(e) => setFormData({...formData, sexe: e.target.value})}
                          className="input-field"
                        >
                          <option value="M">Masculin</option>
                          <option value="F">Féminin</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                        <textarea
                          value={formData.notes}
                          onChange={(e) => setFormData({...formData, notes: e.target.value})}
                          className="input-field"
                          rows="3"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Antécédents</label>
                        <textarea
                          value={formData.antecedents}
                          onChange={(e) => setFormData({...formData, antecedents: e.target.value})}
                          className="input-field"
                          rows="3"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="btn-outline"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    {selectedPatient ? 'Modifier' : 'Créer'}
                  </button>
                </div>
              </form>
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
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations familiales</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Père:</span>
                      <p className="text-gray-900">{selectedPatient.pere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.telephone || ''}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.fonction || ''}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Mère:</span>
                      <p className="text-gray-900">{selectedPatient.mere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.telephone || ''}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.fonction || ''}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">WhatsApp:</span>
                      {selectedPatient.lien_whatsapp ? (
                        <a
                          href={selectedPatient.lien_whatsapp}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 text-green-600 hover:text-green-800"
                        >
                          <MessageCircle className="w-4 h-4" />
                          <span>{selectedPatient.numero_whatsapp}</span>
                        </a>
                      ) : (
                        <p className="text-gray-900">N/A</p>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations médicales</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Notes:</span>
                      <p className="text-gray-900">{selectedPatient.notes || 'Aucune note'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Antécédents:</span>
                      <p className="text-gray-900">{selectedPatient.antecedents || 'Aucun antécédent'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Première consultation:</span>
                      <p className="text-gray-900">{selectedPatient.date_premiere_consultation || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Dernière consultation:</span>
                      <p className="text-gray-900">{selectedPatient.date_derniere_consultation || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Consultations</h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={addNewConsultation}
                        className="flex items-center space-x-1 bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded-lg transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Consultation</span>
                      </button>
                      <button
                        onClick={addNewAppointment}
                        className="flex items-center space-x-1 bg-green-500 hover:bg-green-600 text-white text-sm px-3 py-1 rounded-lg transition-colors"
                      >
                        <CalendarPlus className="w-4 h-4" />
                        <span>RDV</span>
                      </button>
                    </div>
                  </div>
                  
                  {loadingConsultations ? (
                    <div className="flex items-center justify-center h-20">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {consultationDetails.length > 0 ? (
                        <>
                          {consultationDetails.slice(0, 3).map((consultation, index) => (
                            <div key={consultation.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                              <div className="flex items-center space-x-3">
                                <div className="flex flex-col">
                                  <div className="flex items-center space-x-2">
                                    <Stethoscope className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm font-medium text-gray-900">{consultation.date}</span>
                                    <span className={`text-xs px-2 py-1 rounded-full border ${getConsultationTypeColor(consultation.type)}`}>
                                      {consultation.type === 'visite' ? 'Visite' : 'Contrôle'}
                                    </span>
                                  </div>
                                  <div className="text-xs text-gray-600 mt-1">
                                    {consultation.duree > 0 ? `${consultation.duree} min` : 'Durée non spécifiée'}
                                    {consultation.observations && (
                                      <span className="ml-2">• {consultation.observations.substring(0, 40)}{consultation.observations.length > 40 ? '...' : ''}</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => viewSingleConsultation(consultation.id)}
                                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => editConsultation(consultation)}
                                  className="text-green-600 hover:text-green-800 text-sm font-medium"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => deleteConsultation(consultation.id)}
                                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          ))}
                          {consultationDetails.length > 3 && (
                            <div className="text-center pt-2">
                              <button
                                onClick={() => viewConsultationDetails(selectedPatient.id)}
                                className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                              >
                                Voir toutes les consultations ({consultationDetails.length})
                              </button>
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="text-center py-4">
                          <p className="text-gray-500">Aucune consultation trouvée</p>
                          <button 
                            onClick={addNewConsultation}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2"
                          >
                            Créer la première consultation
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowPatientModal(false);
                    openModal(selectedPatient);
                  }}
                  className="btn-outline"
                >
                  Modifier
                </button>
                <button
                  onClick={() => setShowPatientModal(false)}
                  className="btn-primary"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consultation Details Modal */}
      {showConsultationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Historique des consultations
                  {selectedPatient && (
                    <span className="text-lg font-medium text-gray-600 ml-2">
                      - {selectedPatient.prenom} {selectedPatient.nom}
                    </span>
                  )}
                </h2>
                <button
                  onClick={() => setShowConsultationModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  <span className="sr-only">Fermer</span>
                  ×
                </button>
              </div>

              {loadingConsultations ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {consultationDetails.length > 0 ? (
                    consultationDetails.map((consultation, index) => (
                      <div key={consultation.id} className="border rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className="bg-primary-100 p-2 rounded-full">
                              <Clock className="w-4 h-4 text-primary-600" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">{consultation.date}</h3>
                              <p className="text-sm text-gray-600">
                                {consultation.type === 'visite' ? 'Visite' : 'Contrôle'} - 
                                {consultation.duree > 0 ? ` ${consultation.duree} min` : ' Durée non spécifiée'}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              consultation.type === 'visite' 
                                ? 'bg-blue-100 text-blue-800' 
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {consultation.type === 'visite' ? 'Visite' : 'Contrôle'}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Mesures</h4>
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Poids:</span>
                                <span className="font-medium">{consultation.poids > 0 ? `${consultation.poids} kg` : 'Non mesurée'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Taille:</span>
                                <span className="font-medium">{consultation.taille > 0 ? `${consultation.taille} cm` : 'Non mesurée'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">PC:</span>
                                <span className="font-medium">{consultation.pc > 0 ? `${consultation.pc} cm` : 'Non mesurée'}</span>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Résumé</h4>
                            <div className="space-y-1 text-sm">
                              <div>
                                <span className="text-gray-600">Observations:</span>
                                <p className="text-gray-900 mt-1">{consultation.observations || 'Aucune observation'}</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="mt-4 space-y-3">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-1">Traitement</h4>
                            <p className="text-sm text-gray-600 bg-white p-2 rounded">
                              {consultation.traitement || 'Aucun traitement prescrit'}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-1">Bilan</h4>
                            <p className="text-sm text-gray-600 bg-white p-2 rounded">
                              {consultation.bilan || 'Aucun bilan'}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Aucune consultation trouvée
                      </h3>
                      <p className="text-gray-500">
                        Ce patient n'a pas encore d'historique de consultations.
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowConsultationModal(false)}
                  className="btn-primary"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Single Consultation Details Modal */}
      {showConsultationDetailsModal && selectedConsultation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Détails de la consultation
                </h2>
                <button
                  onClick={() => setShowConsultationDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations générales</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date:</span>
                      <p className="text-gray-900">{selectedConsultation.date}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Type:</span>
                      <span className={`ml-2 text-xs px-2 py-1 rounded-full ${getConsultationTypeColor(selectedConsultation.type)}`}>
                        {selectedConsultation.type === 'visite' ? 'Visite' : 'Contrôle'}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Durée:</span>
                      <p className="text-gray-900">{selectedConsultation.duree > 0 ? `${selectedConsultation.duree} minutes` : 'Non spécifiée'}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-700">Poids:</span>
                      <span className="text-gray-900">{selectedConsultation.poids > 0 ? `${selectedConsultation.poids} kg` : 'Non mesuré'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-700">Taille:</span>
                      <span className="text-gray-900">{selectedConsultation.taille > 0 ? `${selectedConsultation.taille} cm` : 'Non mesurée'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-700">PC:</span>
                      <span className="text-gray-900">{selectedConsultation.pc > 0 ? `${selectedConsultation.pc} cm` : 'Non mesuré'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Observations</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultation.observations || 'Aucune observation'}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Traitement</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultation.traitement || 'Aucun traitement'}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Bilan</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedConsultation.bilan || 'Aucun bilan'}
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowConsultationDetailsModal(false);
                    editConsultation(selectedConsultation);
                  }}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                >
                  <Edit className="w-4 h-4" />
                  <span>Modifier</span>
                </button>
                <button
                  onClick={() => setShowConsultationDetailsModal(false)}
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
                {/* Mesures */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Weight className="w-4 h-4 inline mr-1" />
                        Poids (kg)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.poids}
                        onChange={(e) => setConsultationFormData({...consultationFormData, poids: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Ruler className="w-4 h-4 inline mr-1" />
                        Taille (cm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.taille}
                        onChange={(e) => setConsultationFormData({...consultationFormData, taille: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Brain className="w-4 h-4 inline mr-1" />
                        PC (cm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.pc}
                        onChange={(e) => setConsultationFormData({...consultationFormData, pc: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Clock className="w-4 h-4 inline mr-1" />
                        Durée (min)
                      </label>
                      <input
                        type="number"
                        value={consultationFormData.duree}
                        onChange={(e) => setConsultationFormData({...consultationFormData, duree: e.target.value})}
                        className="input-field"
                      />
                    </div>
                  </div>
                </div>

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

      {/* Add Consultation Modal */}
      {showAddConsultationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Nouvelle consultation
                </h2>
                <button
                  onClick={() => setShowAddConsultationModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Mesures */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Weight className="w-4 h-4 inline mr-1" />
                        Poids (kg)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.poids}
                        onChange={(e) => setConsultationFormData({...consultationFormData, poids: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Ruler className="w-4 h-4 inline mr-1" />
                        Taille (cm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.taille}
                        onChange={(e) => setConsultationFormData({...consultationFormData, taille: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Brain className="w-4 h-4 inline mr-1" />
                        PC (cm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={consultationFormData.pc}
                        onChange={(e) => setConsultationFormData({...consultationFormData, pc: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Clock className="w-4 h-4 inline mr-1" />
                        Durée (min)
                      </label>
                      <input
                        type="number"
                        value={consultationFormData.duree}
                        onChange={(e) => setConsultationFormData({...consultationFormData, duree: e.target.value})}
                        className="input-field"
                      />
                    </div>
                  </div>
                </div>

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
                  onClick={() => setShowAddConsultationModal(false)}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
                >
                  Annuler
                </button>
                <button
                  onClick={createConsultation}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Créer</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Memoized component to prevent unnecessary re-renders
const PatientsList = React.memo(({ user }) => {
  return <PatientsListComponent user={user} />;
});

export default PatientsList;