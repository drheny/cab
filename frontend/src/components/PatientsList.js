import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Phone, 
  User,
  MessageCircle,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Calendar
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import AppointmentModal from './AppointmentModal';

const PatientsListComponent = ({ user }) => {
  const location = useLocation();
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
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [appointmentFormData, setAppointmentFormData] = useState({
    patient_id: '',
    date: '',
    heure: '',
    type_rdv: 'visite',
    motif: '',
    notes: '',
    statut: 'programme'
  });
  const searchInputRef = useRef(null);

  // Helper function to convert dd/mm/yyyy to yyyy-mm-dd for search
  const formatDateForSearch = (searchTerm) => {
    // Don't trigger search for incomplete dates
    if (searchTerm.includes('/')) {
      // Only search when we have a complete date pattern
      const datePattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
      const match = searchTerm.match(datePattern);
      
      if (match) {
        const [, day, month, year] = match;
        // Convert to yyyy-mm-dd format for backend search
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
      }
      
      // If incomplete date, return empty string to avoid search
      return '';
    }
    
    return searchTerm;
  };

  // Enhanced search function that handles dates better
  const shouldTriggerSearch = (searchTerm) => {
    // Don't search if empty
    if (!searchTerm.trim()) return false;
    
    // If contains '/', only search if it's a complete date
    if (searchTerm.includes('/')) {
      const datePattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
      return datePattern.test(searchTerm);
    }
    
    // For regular text, search if at least 2 characters
    return searchTerm.length >= 2;
  };
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
        nom: patient.nom || '',
        prenom: patient.prenom || '',
        date_naissance: patient.date_naissance || '',
        adresse: patient.adresse || '',
        pere: {
          nom: patient.pere?.nom || '',
          telephone: patient.pere?.telephone || '',
          fonction: patient.pere?.fonction || ''
        },
        mere: {
          nom: patient.mere?.nom || '',
          telephone: patient.mere?.telephone || '',
          fonction: patient.mere?.fonction || ''
        },
        numero_whatsapp: patient.numero_whatsapp || '',
        notes: patient.notes || '',
        antecedents: patient.antecedents || '',
        sexe: patient.sexe || 'M',
        telephone: patient.telephone || '',
        nom_parent: patient.nom_parent || '',
        telephone_parent: patient.telephone_parent || '',
        assurance: patient.assurance || '',
        numero_assurance: patient.numero_assurance || '',
        allergies: patient.allergies || ''
      });
    } else {
      resetForm();
    }
    setShowModal(true);
  };

  const fetchPatients = useCallback(async (page = 1, search = '') => {
    try {
      setSearchLoading(Boolean(search));
      
      // Only format and search if should trigger search
      const formattedSearch = shouldTriggerSearch(search) ? formatDateForSearch(search) : search;
      
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients`, {
        params: {
          page,
          limit: 10,
          search: formattedSearch || undefined
        }
      });
      
      const { patients: fetchedPatients, total_count: totalCountFromAPI, total_pages: totalPagesFromAPI } = response.data;
      
      setPatients(fetchedPatients || []);
      setTotalCount(totalCountFromAPI || 0);
      setTotalPages(totalPagesFromAPI || 0);
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching patients:', error);
      toast.error('Erreur lors du chargement des patients');
      setPatients([]);
      setTotalCount(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
      setSearchLoading(false);
    }
  }, []);

  // Check URL params for pre-selected patient
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const patientParam = urlParams.get('patient');
    const actionParam = urlParams.get('action');
    
    if (patientParam) {
      // Pre-populate search with patient ID or name
      setSearchTerm(patientParam);
      setDebouncedSearchTerm(patientParam);
    }
    
    // Handle action parameter for opening modal
    if (actionParam === 'add') {
      openModal(); // Open new patient modal
    }
  }, [location.search]);

  // Load initial patients
  useEffect(() => {
    fetchPatients(1, debouncedSearchTerm);
  }, [fetchPatients, debouncedSearchTerm]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Reset to page 1 when search changes
  useEffect(() => {
    if (debouncedSearchTerm !== searchTerm) return;
    fetchPatients(1, debouncedSearchTerm);
  }, [debouncedSearchTerm, fetchPatients]);

  // Page change handler
  useEffect(() => {
    if (currentPage > 1) {
      fetchPatients(currentPage, debouncedSearchTerm);
    }
  }, [currentPage, fetchPatients, debouncedSearchTerm]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const handleSearch = useCallback((e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  }, []);

  // Memoize search input props to prevent unnecessary re-renders
  const searchInputProps = useMemo(() => ({
    ref: searchInputRef,
    type: "text",
    placeholder: "Rechercher par nom, prénom ou date de naissance (dd/mm/yyyy) - Écriture manuscrite supportée",
    defaultValue: searchTerm,
    onChange: handleSearch,
    className: "search-stylus w-full pl-8 sm:pl-10 pr-4",
    inputMode: "text",
    autoCapitalize: "words",
    autoComplete: "off",
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

  const handleDeletePatient = useCallback(async (patientId) => {
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
  }, [fetchPatients]);

  const openAppointmentModal = (patient) => {
    // Pré-remplir les données du RDV avec le patient sélectionné
    setAppointmentFormData({
      patient_id: patient.id,
      date: '',
      heure: '',
      type_rdv: 'visite',
      motif: '',
      notes: '',
      statut: 'programme'
    });
    setSelectedPatient(patient);
    setShowAppointmentModal(true);
  };

  const handleSaveAppointment = async (formData) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/appointments`, formData);
      
      if (response.status === 200 || response.status === 201) {
        toast.success(`Rendez-vous créé avec succès pour ${selectedPatient.prenom} ${selectedPatient.nom}`);
        setShowAppointmentModal(false);
        setSelectedPatient(null);
        setAppointmentFormData({
          patient_id: '',
          date: '',
          heure: '',
          type_rdv: 'visite',
          motif: '',
          notes: '',
          statut: 'programme'
        });
        return { success: true };
      } else {
        return { success: false, error: 'Erreur lors de la création du rendez-vous' };
      }
    } catch (error) {
      console.error('Error creating appointment:', error);
      return { success: false, error: error.response?.data?.detail || 'Erreur lors de la création du rendez-vous' };
    }
  };

  const viewPatientDetails = async (patientId) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/patients/${patientId}`);
      setSelectedPatient(response.data);
      setShowPatientModal(true);
    } catch (error) {
      console.error('Error fetching patient details:', error);
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
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => openAppointmentModal(patient)}
                  className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                  title="Ajouter RDV"
                >
                  <Calendar className="w-4 h-4" />
                </button>
                <button
                  onClick={() => openModal(patient)}
                  className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
                  title="Modifier patient"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeletePatient(patient.id)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                  title="Supprimer patient"
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
                onClick={() => openAppointmentModal(patient)}
                className="p-1.5 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                title="Ajouter RDV"
              >
                <Calendar className="w-4 h-4" />
              </button>
              <button
                onClick={() => openModal(patient)}
                className="p-1.5 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
                title="Modifier patient"
              >
                <Edit className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDeletePatient(patient.id)}
                className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                title="Supprimer patient"
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
                className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
                title="Envoyer WhatsApp"
              >
                <MessageCircle className="w-4 h-4" />
              </a>
            ) : (
              <span className="p-1 text-gray-400">
                <MessageCircle className="w-4 h-4" />
              </span>
            )}
          </div>
        </div>
      </div>
    ));
  }, [patients, handleDeletePatient, openAppointmentModal]);

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
                          className="input-stylus"
                          placeholder="Nom de famille - Écriture manuscrite supportée"
                          inputMode="text"
                          autoCapitalize="words"
                          autoComplete="family-name"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Prénom *</label>
                        <input
                          type="text"
                          value={formData.prenom}
                          onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                          className="input-stylus"
                          placeholder="Prénom - Écriture manuscrite supportée"
                          inputMode="text"
                          autoCapitalize="words"
                          autoComplete="given-name"
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
                          className="input-stylus"
                          placeholder="Adresse complète - Écriture manuscrite supportée"
                          inputMode="text"
                          autoCapitalize="words"
                          autoComplete="street-address"
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
                              className="input-stylus"
                              placeholder="Nom du père - Écriture manuscrite supportée"
                              inputMode="text"
                              autoCapitalize="words"
                              autoComplete="name"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                            <input
                              type="tel"
                              value={formData.pere.telephone}
                              onChange={(e) => setFormData({...formData, pere: {...formData.pere, telephone: e.target.value}})}
                              className="input-stylus"
                              placeholder="Numéro du père - Écriture manuscrite supportée"
                              inputMode="tel"
                              autoComplete="tel"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Fonction</label>
                            <input
                              type="text"
                              value={formData.pere.fonction}
                              onChange={(e) => setFormData({...formData, pere: {...formData.pere, fonction: e.target.value}})}
                              className="input-stylus"
                              placeholder="Profession du père - Écriture manuscrite supportée"
                              inputMode="text"
                              autoCapitalize="words"
                              autoComplete="organization-title"
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
                              className="input-stylus"
                              placeholder="Nom de la mère - Écriture manuscrite supportée"
                              inputMode="text"
                              autoCapitalize="words"
                              autoComplete="name"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                            <input
                              type="tel"
                              value={formData.mere.telephone}
                              onChange={(e) => setFormData({...formData, mere: {...formData.mere, telephone: e.target.value}})}
                              className="input-stylus"
                              placeholder="Numéro de la mère - Écriture manuscrite supportée"
                              inputMode="tel"
                              autoComplete="tel"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Fonction</label>
                            <input
                              type="text"
                              value={formData.mere.fonction}
                              onChange={(e) => setFormData({...formData, mere: {...formData.mere, fonction: e.target.value}})}
                              className="input-stylus"
                              placeholder="Profession de la mère - Écriture manuscrite supportée"
                              inputMode="text"
                              autoCapitalize="words"
                              autoComplete="organization-title"
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
                          className="input-stylus"
                          placeholder="216xxxxxxxx - Écriture manuscrite supportée"
                          inputMode="tel"
                          autoComplete="tel"
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
                          className="textarea-stylus"
                          placeholder="Notes générales - Optimisé pour Apple Pencil"
                          inputMode="text"
                          autoCapitalize="sentences"
                          rows="3"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Antécédents</label>
                        <textarea
                          value={formData.antecedents}
                          onChange={(e) => setFormData({...formData, antecedents: e.target.value})}
                          className="textarea-stylus"
                          placeholder="Antécédents médicaux - Optimisé pour Apple Pencil"
                          inputMode="text"
                          autoCapitalize="sentences"
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
                  Détails du patient
                </h2>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => viewPatientConsultations(selectedPatient.id, `${selectedPatient.prenom} ${selectedPatient.nom}`)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>Voir Consultations</span>
                  </button>
                  <button
                    onClick={() => setShowPatientModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Informations de base */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations personnelles</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Nom complet:</span>
                      <p className="text-gray-900">{selectedPatient.prenom} {selectedPatient.nom}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Date de naissance:</span>
                      <p className="text-gray-900">{formatDate(selectedPatient.date_naissance)}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Âge:</span>
                      <p className="text-gray-900">{selectedPatient.age || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Sexe:</span>
                      <p className="text-gray-900">{selectedPatient.sexe === 'M' ? 'Masculin' : 'Féminin'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Adresse:</span>
                      <p className="text-gray-900">{selectedPatient.adresse || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Informations de contact */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Père:</span>
                      <p className="text-gray-900">{selectedPatient.pere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.telephone || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.pere?.fonction || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Mère:</span>
                      <p className="text-gray-900">{selectedPatient.mere?.nom || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.telephone || 'N/A'}</p>
                      <p className="text-sm text-gray-600">{selectedPatient.mere?.fonction || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">WhatsApp:</span>
                      {selectedPatient.lien_whatsapp ? (
                        <a
                          href={selectedPatient.lien_whatsapp}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-800"
                        >
                          Contacter
                        </a>
                      ) : (
                        <p className="text-gray-900">N/A</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Informations médicales */}
                <div className="md:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations médicales</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Notes:</span>
                      <p className="text-gray-900 whitespace-pre-wrap">{selectedPatient.notes || 'Aucune note'}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Antécédents:</span>
                      <p className="text-gray-900 whitespace-pre-wrap">{selectedPatient.antecedents || 'Aucun antécédent'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Appointment Modal */}
      {showAppointmentModal && selectedPatient && (
        <AppointmentModal
          isOpen={showAppointmentModal}
          onClose={() => {
            setShowAppointmentModal(false);
            setSelectedPatient(null);
          }}
          onSave={handleSaveAppointment}
          formData={appointmentFormData}
          setFormData={setAppointmentFormData}
          selectedPatient={selectedPatient}
        />
      )}
    </div>
  );
};

export default PatientsListComponent;