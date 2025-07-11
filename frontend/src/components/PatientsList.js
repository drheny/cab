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
  Users
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const PatientsList = ({ user }) => {
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

  const handleSearch = (e) => {
    const value = e.target.value;
    const cursorPosition = e.target.selectionStart;
    
    setSearchTerm(value);
    
    // Preserve cursor position without causing re-render
    requestAnimationFrame(() => {
      if (searchInputRef.current) {
        searchInputRef.current.setSelectionRange(cursorPosition, cursorPosition);
      }
    });
  };

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
    } catch (error) {
      console.error('Error fetching patient details:', error);
      toast.error('Erreur lors du chargement des détails du patient');
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

      {/* Search with loading indicator */}
      <div className="relative mb-4 sm:mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 sm:w-5 sm:h-5" />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Rechercher par nom, prénom ou date de naissance..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full pl-8 sm:pl-10 pr-4 py-2 sm:py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 responsive-text"
        />
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
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Consultations</h3>
                  <div className="space-y-2">
                    {selectedPatient.consultations && selectedPatient.consultations.length > 0 ? (
                      selectedPatient.consultations.map((consultation, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{consultation.date}</p>
                            <p className="text-xs text-gray-600">{consultation.type}</p>
                          </div>
                          <button className="text-primary-600 hover:text-primary-800 text-sm">
                            Voir détails
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-500">Aucune consultation</p>
                    )}
                  </div>
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
    </div>
  );
};

// Memoized component to prevent unnecessary re-renders
const PatientsList = React.memo(({ user }) => {
  return <PatientsListComponent user={user} />;
});

export default PatientsList;