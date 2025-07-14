import React, { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Calendar as CalendarIcon, 
  Plus, 
  Edit, 
  Trash2, 
  Clock, 
  User,
  MessageCircle,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  List,
  Grid,
  CheckCircle,
  DollarSign,
  X,
  ChevronUp,
  ChevronDown,
  AlertTriangle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import AppointmentModal from './AppointmentModal';

const Calendar = ({ user }) => {
  const location = useLocation();
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'week'
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [showModal, setShowModal] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [weekData, setWeekData] = useState({ week_dates: [], appointments: [] });
  
  // Patient modal states
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showPatientModal, setShowPatientModal] = useState(false);
  
  // Form states
  const [formData, setFormData] = useState({
    patient_id: '',
    date: '',
    heure: '',
    type_rdv: 'visite',
    motif: '',
    notes: ''
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  const resetForm = () => {
    setFormData({
      patient_id: '',
      date: selectedDate,
      heure: '',
      type_rdv: 'visite',
      motif: '',
      notes: ''
    });
    setSelectedAppointment(null);
  };

  const openModal = (appointment = null) => {
    if (appointment) {
      setSelectedAppointment(appointment);
      setFormData({
        patient_id: appointment.patient_id,
        date: appointment.date,
        heure: appointment.heure,
        type_rdv: appointment.type_rdv,
        motif: appointment.motif || '',
        notes: appointment.notes || ''
      });
    } else {
      resetForm();
    }
    setShowModal(true);
  };

  const openModalWithDateTime = (dateTime = {}) => {
    resetForm();
    setFormData({
      ...formData,
      date: dateTime.date || selectedDate,
      heure: dateTime.heure || ''
    });
    setShowModal(true);
  };

  useEffect(() => {
    fetchData();
    
    // Auto-open modal from Dashboard quick action
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('action') === 'add') {
      openModal();
      window.history.replaceState({}, '', '/calendar');
    }
  }, [selectedDate, viewMode]); // openModal is defined later, will be handled by React

  const fetchData = async () => {
    setLoading(true);
    try {
      if (viewMode === 'list') {
        // Fetch data for day view
        const [appointmentsRes, patientsRes, statsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/rdv/jour/${selectedDate}`),
          axios.get(`${API_BASE_URL}/api/patients`),
          axios.get(`${API_BASE_URL}/api/rdv/stats/${selectedDate}`)
        ]);
        setAppointments(appointmentsRes.data || []);
        setPatients(patientsRes.data.patients || []);
        setStats(statsRes.data || {});
      } else {
        // Fetch data for week view
        const [weekRes, patientsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/rdv/semaine/${selectedDate}`),
          axios.get(`${API_BASE_URL}/api/patients`)
        ]);
        setWeekData(weekRes.data || { week_dates: [], appointments: [] });
        setPatients(patientsRes.data.patients || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAppointment = async () => {
    try {
      console.log('Creating appointment with formData:', formData);
      const response = await axios.post(`${API_BASE_URL}/api/appointments`, formData);
      console.log('Appointment created successfully:', response.data);
      toast.success('Rendez-vous créé avec succès');
      setShowModal(false);
      resetForm();
      // Rafraîchir les données du calendrier
      await fetchData();
    } catch (error) {
      console.error('Error creating appointment:', error);
      console.error('Error details:', error.response?.data);
      toast.error('Erreur lors de la création du rendez-vous: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdateAppointment = async () => {
    try {
      await axios.put(`${API_BASE_URL}/api/appointments/${selectedAppointment.id}`, formData);
      toast.success('Rendez-vous mis à jour avec succès');
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Error updating appointment:', error);
      toast.error('Erreur lors de la mise à jour du rendez-vous');
    }
  };

  const handleDeleteAppointment = async (appointmentId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce rendez-vous ?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/appointments/${appointmentId}`);
        toast.success('Rendez-vous supprimé avec succès');
        fetchData();
      } catch (error) {
        console.error('Error deleting appointment:', error);
        toast.error('Erreur lors de la suppression du rendez-vous');
      }
    }
  };

  const handleStatusUpdate = async (appointmentId, newStatus) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { statut: newStatus });
      toast.success('Statut mis à jour');
      fetchData();
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  const handleRoomAssignment = async (appointmentId, salle) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/salle`, { salle });
      toast.success(`Affecté à ${salle === 'salle1' ? 'Salle 1' : salle === 'salle2' ? 'Salle 2' : 'aucune salle'}`);
      fetchData();
    } catch (error) {
      console.error('Error updating room:', error);
      toast.error('Erreur lors de l\'affectation de salle');
    }
  };

  const handlePatientArrival = async (appointmentId, salle) => {
    try {
      // Marquer le patient comme arrivé et l'affecter à la salle
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { statut: 'attente' });
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/salle`, { salle });
      toast.success(`Patient arrivé et affecté à ${salle === 'salle1' ? 'Salle 1' : 'Salle 2'}`);
      fetchData();
    } catch (error) {
      console.error('Error handling patient arrival:', error);
      toast.error('Erreur lors de la prise en charge du patient');
    }
  };

  // ====== NOUVELLES FONCTIONS WORKFLOW ======
  
  // Basculer entre Contrôle/Visite
  const handleTypeToggle = async (appointmentId, currentType) => {
    try {
      const newType = currentType === 'visite' ? 'controle' : 'visite';
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}`, { type_rdv: newType });
      
      // Si on change vers contrôle, mettre automatiquement en gratuit
      if (newType === 'controle') {
        await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/paiement`, {
          paye: false,
          gratuit: true,
          montant: 0,
          methode_paiement: ''
        });
      }
      
      toast.success(`Type changé vers ${newType === 'visite' ? 'Visite' : 'Contrôle'}`);
      fetchData();
    } catch (error) {
      console.error('Error toggling type:', error);
      toast.error('Erreur lors du changement de type');
    }
  };

  // Démarrer consultation (attente → en_cours)
  const handleStartConsultation = async (appointmentId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { statut: 'en_cours' });
      toast.success('Consultation démarrée');
      fetchData();
    } catch (error) {
      console.error('Error starting consultation:', error);
      toast.error('Erreur lors du démarrage de la consultation');
    }
  };

  // Terminer consultation (en_cours → termine)
  const handleFinishConsultation = async (appointmentId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { statut: 'termine' });
      toast.success('Consultation terminée');
      fetchData();
    } catch (error) {
      console.error('Error finishing consultation:', error);
      toast.error('Erreur lors de la fin de consultation');
    }
  };

  // Gestion des paiements
  const handlePaymentUpdate = async (appointmentId, paymentData) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/paiement`, paymentData);
      toast.success('Paiement mis à jour');
      fetchData();
    } catch (error) {
      console.error('Error updating payment:', error);
      toast.error('Erreur lors de la mise à jour du paiement');
    }
  };

  // ====== FONCTIONS RÉORGANISATION SALLE D'ATTENTE ======
  
  // Monter un patient dans la liste d'attente
  const handleMoveUp = async (appointmentId) => {
    try {
      const waitingPatients = groupedAppointments.attente;
      const currentIndex = waitingPatients.findIndex(apt => apt.id === appointmentId);
      
      if (currentIndex > 0) {
        // Échanger les positions avec le patient au-dessus
        const patientAbove = waitingPatients[currentIndex - 1];
        
        await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/priority`, { 
          action: 'move_up',
          target_id: patientAbove.id 
        });
        
        toast.success('Patient déplacé vers le haut');
        fetchData();
      }
    } catch (error) {
      console.error('Error moving patient up:', error);
      toast.error('Erreur lors du déplacement');
    }
  };

  // Descendre un patient dans la liste d'attente
  const handleMoveDown = async (appointmentId) => {
    try {
      const waitingPatients = groupedAppointments.attente;
      const currentIndex = waitingPatients.findIndex(apt => apt.id === appointmentId);
      
      if (currentIndex < waitingPatients.length - 1) {
        // Échanger les positions avec le patient en-dessous
        const patientBelow = waitingPatients[currentIndex + 1];
        
        await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/priority`, { 
          action: 'move_down',
          target_id: patientBelow.id 
        });
        
        toast.success('Patient déplacé vers le bas');
        fetchData();
      }
    } catch (error) {
      console.error('Error moving patient down:', error);
      toast.error('Erreur lors du déplacement');
    }
  };

  // Mettre un patient en priorité (premier dans la liste)
  const handleSetPriority = async (appointmentId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/priority`, { 
        action: 'set_first' 
      });
      
      toast.success('Patient mis en priorité');
      fetchData();
    } catch (error) {
      console.error('Error setting priority:', error);
      toast.error('Erreur lors de la mise en priorité');
    }
  };

  // États pour les modales
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showStatusDropdown, setShowStatusDropdown] = useState(null);
  const [showRoomDropdown, setShowRoomDropdown] = useState(null);

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

  const getStatusColor = (status) => {
    switch (status) {
      case 'absent': return 'bg-gray-100 text-gray-800';
      case 'attente': return 'bg-yellow-100 text-yellow-800';
      case 'en_cours': return 'bg-blue-100 text-blue-800';
      case 'termine': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'absent': return 'Absent';
      case 'attente': return 'En attente';
      case 'en_cours': return 'En cours';
      case 'termine': return 'Terminé';
      default: return 'Absent';
    }
  };

  const getWhatsAppLink = (phone) => {
    const cleanPhone = phone.replace(/\D/g, '');
    return `https://wa.me/212${cleanPhone.startsWith('0') ? cleanPhone.substring(1) : cleanPhone}`;
  };

  const navigateDate = (direction) => {
    const currentDate = new Date(selectedDate);
    if (direction === 'prev') {
      currentDate.setDate(currentDate.getDate() - 1);
    } else {
      currentDate.setDate(currentDate.getDate() + 1);
    }
    setSelectedDate(currentDate.toISOString().split('T')[0]);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Sort appointments by status priority for list view
  const sortedAppointments = useMemo(() => {
    if (!appointments) return [];
    
    const statusOrder = {
      'programme': 1,
      'attente': 2, 
      'en_cours': 3,
      'retard': 4,
      'absent': 5,
      'termine': 6
    };
    
    return [...appointments].sort((a, b) => {
      // First sort by status priority
      const statusDiff = (statusOrder[a.statut] || 0) - (statusOrder[b.statut] || 0);
      if (statusDiff !== 0) return statusDiff;
      
      // Then by time
      return a.heure.localeCompare(b.heure);
    });
  }, [appointments]);

  const groupedAppointments = useMemo(() => {
    const groups = {
      attente: [],
      en_cours: [],
      absent: [],
      retard: [],
      termine: []
    };
    
    sortedAppointments.forEach(apt => {
      // Auto-assign à la section appropriée selon la logique métier
      let targetSection = apt.statut;
      
      // Les RDV programmés (non encore venus) vont dans "absent non encore venu"
      if (apt.statut === 'programme') {
        targetSection = 'absent';
      }
      
      if (groups[targetSection]) {
        groups[targetSection].push(apt);
      }
    });
    
    return groups;
  }, [sortedAppointments]);

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
          <h1 className="text-2xl font-bold text-gray-900">Calendrier</h1>
          <p className="text-gray-600">Gestion des rendez-vous</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="flex bg-white border border-gray-200 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'list' 
                  ? 'bg-primary-500 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <List className="w-4 h-4" />
              <span>Liste</span>
            </button>
            <button
              onClick={() => setViewMode('week')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'week' 
                  ? 'bg-primary-500 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Grid className="w-4 h-4" />
              <span>Semaine</span>
            </button>
          </div>
          
          <button
            onClick={() => openModal()}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Nouveau RDV</span>
          </button>
        </div>
      </div>

      {/* Date Navigation */}
      <div className="flex items-center justify-between bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <button
          onClick={() => navigateDate('prev')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="input-field"
          />
          <div className="text-center">
            <h2 className="text-lg font-semibold text-gray-900">
              {formatDate(selectedDate)}
            </h2>
          </div>
        </div>
        
        <button
          onClick={() => navigateDate('next')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Statistics for List View */}
      {viewMode === 'list' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center space-x-3">
              <CalendarIcon className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">Total RDV</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_rdv || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center space-x-3">
              <User className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">Visites</p>
                <p className="text-2xl font-bold text-gray-900">{stats.visites || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-8 h-8 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600">Contrôles</p>
                <p className="text-2xl font-bold text-gray-900">{stats.controles || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center space-x-3">
              <Clock className="w-8 h-8 text-orange-500" />
              <div>
                <p className="text-sm text-gray-600">RDV restants</p>
                <p className="text-2xl font-bold text-gray-900">{(stats.statuts?.programme || 0) + (stats.statuts?.retard || 0)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* List View - Workflow Optimisé - Toutes les sections toujours visibles */}
      {viewMode === 'list' && (
        <div className="space-y-6">
          {/* 1. Salle d'attente (en haut) */}
          <WorkflowSection
            title="🟢 Salle d'attente"
            appointments={groupedAppointments.attente}
            sectionType="attente"
            onStatusUpdate={handleStatusUpdate}
            onRoomAssignment={handleRoomAssignment}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onStartConsultation={handleStartConsultation}
            onMoveUp={handleMoveUp}
            onMoveDown={handleMoveDown}
            onSetPriority={handleSetPriority}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
          />
          
          {/* 2. En consultation */}
          <WorkflowSection
            title="🔵 En consultation"
            appointments={groupedAppointments.en_cours}
            sectionType="en_cours"
            onStatusUpdate={handleStatusUpdate}
            onRoomAssignment={handleRoomAssignment}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onFinishConsultation={handleFinishConsultation}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
          />
          
          {/* 3. En retard */}
          <WorkflowSection
            title="🟠 En retard"
            appointments={groupedAppointments.retard}
            sectionType="retard"
            onStatusUpdate={handleStatusUpdate}
            onRoomAssignment={handleRoomAssignment}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onStartConsultation={handleStartConsultation}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
          />
          
          {/* 4. Absents non encore venus */}
          <WorkflowSection
            title="🔴 Absents non encore venus"
            appointments={groupedAppointments.absent}
            sectionType="absent"
            onStatusUpdate={handleStatusUpdate}
            onRoomAssignment={handleRoomAssignment}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
          />
          
          {/* 5. Terminé (en bas) */}
          <WorkflowSection
            title="✅ Terminé"
            appointments={groupedAppointments.termine}
            sectionType="termine"
            onStatusUpdate={handleStatusUpdate}
            onRoomAssignment={handleRoomAssignment}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            isCompleted={true}
          />
          
          {/* Empty state */}
          {appointments.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <CalendarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">Aucun rendez-vous pour cette date</p>
              <button
                onClick={() => openModal()}
                className="mt-4 btn-primary inline-flex items-center space-x-2"
              >
                <Plus className="w-5 h-5" />
                <span>Créer un rendez-vous</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Week View */}
      {viewMode === 'week' && (
        <WeekView
          weekData={weekData}
          onStatusUpdate={handleStatusUpdate}
          onRoomAssignment={handleRoomAssignment}
          onPatientArrival={handlePatientArrival}
          onEdit={openModal}
          onDelete={handleDeleteAppointment}
          onViewPatient={viewPatientDetails}
          onCreateAppointment={openModalWithDateTime}
          selectedDate={selectedDate}
        />
      )}

      {/* Modal */}
      {showModal && (
        <AppointmentModal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          appointment={selectedAppointment}
          patients={patients}
          formData={formData}
          setFormData={setFormData}
          onSave={selectedAppointment ? handleUpdateAppointment : handleCreateAppointment}
          onRefresh={fetchData}
        />
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

// Composant WeekView pour la vue semaine
const WeekView = ({ weekData, onStatusUpdate, onRoomAssignment, onEdit, onDelete, onViewPatient, selectedDate, onCreateAppointment }) => {
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, appointment: null });
  const [hoveredSlot, setHoveredSlot] = useState(null);

  const timeSlots = [];
  for (let hour = 9; hour < 18; hour++) {
    for (let minute = 0; minute < 60; minute += 15) {
      timeSlots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
  }

  const dayNames = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
  
  const getAppointmentsForDateAndTime = (date, time) => {
    return weekData.appointments?.filter(apt => apt.date === date && apt.heure === time) || [];
  };

  const formatDateShort = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'programme': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'attente': return 'bg-green-100 text-green-800 border-green-200';
      case 'en_cours': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'termine': return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'absent': return 'bg-red-100 text-red-800 border-red-200';
      case 'retard': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleSlotClick = (date, time) => {
    // Click sur créneau vide → Nouveau RDV avec date/heure pré-remplie
    onCreateAppointment({
      date: date,
      heure: time
    });
  };

  const handleAppointmentDoubleClick = (appointment) => {
    // Double-click RDV → Edit rapide
    onEdit(appointment);
  };

  const handleRightClick = (e, appointment) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      appointment: appointment
    });
  };

  const handleContextMenuAction = (action) => {
    const { appointment } = contextMenu;
    setContextMenu({ show: false, x: 0, y: 0, appointment: null });

    switch (action) {
      case 'edit':
        onEdit(appointment);
        break;
      case 'delete':
        onDelete(appointment.id);
        break;
      case 'duplicate':
        // Créer un nouvel RDV avec les mêmes données
        onCreateAppointment({
          patient_id: appointment.patient_id,
          date: appointment.date,
          heure: appointment.heure,
          type_rdv: appointment.type_rdv,
          motif: appointment.motif,
          notes: appointment.notes
        });
        break;
      default:
        break;
    }
  };

  const getSlotDensityColor = (appointments) => {
    const count = appointments.length;
    if (count === 0) return 'bg-green-50 hover:bg-green-100'; // Libre
    if (count <= 2) return 'bg-orange-50 hover:bg-orange-100'; // Normal
    return 'bg-red-50 hover:bg-red-100'; // Saturé (3 RDV)
  };

  // Fermer le menu contextuel en cliquant ailleurs
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu({ show: false, x: 0, y: 0, appointment: null });
    };

    if (contextMenu.show) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenu.show]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Vue Semaine</h3>
        <p className="text-sm text-gray-600">Lundi → Samedi • 9h00 → 18h00 • Click créneau vide pour nouveau RDV</p>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          {/* Header with days */}
          <div className="grid grid-cols-7 border-b border-gray-200">
            <div className="p-3 bg-gray-50 border-r border-gray-200">
              <span className="text-sm font-medium text-gray-500">Heure</span>
            </div>
            {weekData.week_dates?.map((date, index) => (
              <div key={date} className="p-3 bg-gray-50 border-r border-gray-200 last:border-r-0">
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900">{dayNames[index]}</div>
                  <div className="text-xs text-gray-500">{formatDateShort(date)}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Time slots grid */}
          <div className="max-h-96 overflow-y-auto">
            {timeSlots.map((time) => (
              <div key={time} className="grid grid-cols-7 border-b border-gray-100">
                {/* Time column */}
                <div className="p-2 border-r border-gray-200 bg-gray-50">
                  <span className="text-xs text-gray-600 font-mono">{time}</span>
                </div>
                
                {/* Days columns */}
                {weekData.week_dates?.map((date) => {
                  const appointments = getAppointmentsForDateAndTime(date, time);
                  const isSlotFull = appointments.length >= 3;
                  
                  return (
                    <div 
                      key={`${date}-${time}`} 
                      className={`p-1 border-r border-gray-100 last:border-r-0 min-h-[60px] cursor-pointer transition-colors ${getSlotDensityColor(appointments)}`}
                      onClick={() => !isSlotFull && handleSlotClick(date, time)}
                      onMouseEnter={() => setHoveredSlot({ date, time, appointments })}
                      onMouseLeave={() => setHoveredSlot(null)}
                      title={appointments.length === 0 ? 'Cliquer pour nouveau RDV' : `${appointments.length}/3 RDV`}
                    >
                      {/* Appointments dans le créneau (max 3) */}
                      <div className="space-y-1">
                        {appointments.slice(0, 3).map((apt, index) => (
                          <div
                            key={apt.id}
                            className={`text-xs p-1 rounded border cursor-pointer hover:shadow-sm transition-all relative ${getStatusColor(apt.statut)}`}
                            onDoubleClick={(e) => {
                              e.stopPropagation();
                              handleAppointmentDoubleClick(apt);
                            }}
                            onContextMenu={(e) => {
                              e.stopPropagation();
                              handleRightClick(e, apt);
                            }}
                            onClick={(e) => e.stopPropagation()}
                            title={`${apt.patient?.prenom} ${apt.patient?.nom} - Double-click: Modifier | Right-click: Menu`}
                          >
                            <div className="truncate">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onViewPatient(apt.patient_id);
                                }}
                                className="font-medium text-gray-900 hover:text-primary-600 transition-colors cursor-pointer underline"
                              >
                                {apt.patient?.prenom} {apt.patient?.nom}
                              </button>
                            </div>
                            <div className="flex items-center space-x-1">
                              <span className={`px-1 py-0.5 rounded text-xs ${
                                apt.type_rdv === 'visite' ? 'bg-blue-200 text-blue-800' : 'bg-green-200 text-green-800'
                              }`}>
                                {apt.type_rdv === 'visite' ? 'V' : 'C'}
                              </span>
                              {apt.salle && (
                                <span className="px-1 py-0.5 rounded text-xs bg-purple-200 text-purple-800">
                                  {apt.salle === 'salle1' ? 'S1' : 'S2'}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                        
                        {/* Indicateur si plus de 3 RDV */}
                        {appointments.length > 3 && (
                          <div className="text-xs text-gray-500 font-medium">
                            +{appointments.length - 3} autres...
                          </div>
                        )}
                        
                        {/* Indicateur créneau libre */}
                        {appointments.length === 0 && (
                          <div className="text-xs text-gray-400 italic">
                            Cliquer pour RDV
                          </div>
                        )}
                        
                        {/* Indicateur places restantes */}
                        {appointments.length > 0 && appointments.length < 3 && (
                          <div className="text-xs text-gray-500">
                            {3 - appointments.length} place{3 - appointments.length > 1 ? 's' : ''} libre{3 - appointments.length > 1 ? 's' : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tooltip Hover */}
      {hoveredSlot && (
        <div className="fixed bg-gray-900 text-white text-sm p-3 rounded-lg shadow-xl z-[9998] pointer-events-none max-w-xs"
             style={{ 
               left: '20px', 
               top: '20px'
             }}>
          <div className="font-medium">{hoveredSlot.time} - {formatDateShort(hoveredSlot.date)}</div>
          <div className="text-gray-300">{hoveredSlot.appointments.length}/3 RDV programmés</div>
          {hoveredSlot.appointments.length === 0 ? (
            <div className="text-green-300 text-xs mt-1">✨ Créneau libre - Cliquer pour nouveau RDV</div>
          ) : hoveredSlot.appointments.length < 3 ? (
            <div className="text-blue-300 text-xs mt-1">📅 {3 - hoveredSlot.appointments.length} place{3 - hoveredSlot.appointments.length > 1 ? 's' : ''} disponible{3 - hoveredSlot.appointments.length > 1 ? 's' : ''}</div>
          ) : (
            <div className="text-red-300 text-xs mt-1">🚫 Créneau complet</div>
          )}
        </div>
      )}

      {/* Menu Contextuel */}
      {contextMenu.show && (
        <div 
          className="fixed bg-white border border-gray-200 rounded-lg shadow-xl z-[9999] py-2 min-w-[150px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleContextMenuAction('edit')}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm transition-colors"
          >
            ✏️ Modifier
          </button>
          <button
            onClick={() => handleContextMenuAction('duplicate')}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm transition-colors"
          >
            📋 Dupliquer
          </button>
          <hr className="my-1" />
          <button
            onClick={() => handleContextMenuAction('delete')}
            className="w-full text-left px-4 py-2 hover:bg-red-50 text-sm text-red-600 transition-colors"
          >
            🗑️ Supprimer
          </button>
        </div>
      )}

      {/* Week Summary */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-600">
            Total rendez-vous de la semaine: <span className="font-medium">{weekData.appointments?.length || 0}</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-green-50 border border-green-200"></div>
              <span className="text-gray-600">Libre</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-orange-50 border border-orange-200"></div>
              <span className="text-gray-600">Normal (1-2)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-red-50 border border-red-200"></div>
              <span className="text-gray-600">Saturé (3)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ====== NOUVEAUX COMPOSANTS WORKFLOW OPTIMISÉS ======

// Composant WorkflowSection pour les 5 sections du workflow
const WorkflowSection = ({ 
  title, 
  appointments, 
  sectionType,
  onStatusUpdate, 
  onRoomAssignment,
  onTypeToggle,
  onPaymentUpdate,
  onStartConsultation,
  onFinishConsultation,
  onEdit, 
  onDelete, 
  onViewPatient,
  isCompleted = false 
}) => {
  const getSectionColor = () => {
    switch (sectionType) {
      case 'attente': return 'border-green-200 bg-green-50';
      case 'en_cours': return 'border-blue-200 bg-blue-50';
      case 'absent': return 'border-red-200 bg-red-50';
      case 'retard': return 'border-orange-200 bg-orange-50';
      case 'termine': return 'border-gray-200 bg-gray-50';
      default: return 'border-gray-200 bg-white';
    }
  };

  return (
    <div className={`rounded-xl shadow-sm border-2 ${getSectionColor()} ${isCompleted ? 'opacity-75' : ''}`}>
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600">{appointments.length} patient(s)</p>
      </div>
      
      <div className="divide-y divide-gray-100">
        {appointments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">👥</div>
            <p>Aucun patient dans cette section</p>
          </div>
        ) : (
          appointments.map((appointment) => (
            <WorkflowCard
              key={appointment.id}
              appointment={appointment}
              sectionType={sectionType}
              onStatusUpdate={onStatusUpdate}
              onRoomAssignment={onRoomAssignment}
              onTypeToggle={onTypeToggle}
              onPaymentUpdate={onPaymentUpdate}
              onStartConsultation={onStartConsultation}
              onFinishConsultation={onFinishConsultation}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewPatient={onViewPatient}
              isCompleted={isCompleted}
            />
          ))
        )}
      </div>
    </div>
  );
};

// Composant WorkflowCard optimisé avec badges interactifs
const WorkflowCard = ({ 
  appointment, 
  sectionType,
  onStatusUpdate, 
  onRoomAssignment,
  onTypeToggle,
  onPaymentUpdate,
  onStartConsultation,
  onFinishConsultation,
  onEdit, 
  onDelete, 
  onViewPatient,
  isCompleted 
}) => {
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const [showRoomDropdown, setShowRoomDropdown] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [waitingTime, setWaitingTime] = useState(0);

  // Calculer temps d'attente pour patients en attente
  useEffect(() => {
    if (sectionType === 'attente') {
      const startTime = new Date(`2025-01-01 ${appointment.heure}`);
      const now = new Date();
      const currentTime = new Date(`2025-01-01 ${now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`);
      const diffMinutes = Math.max(0, Math.floor((currentTime - startTime) / 60000));
      setWaitingTime(diffMinutes);
      
      // Mettre à jour toutes les minutes
      const interval = setInterval(() => {
        const newNow = new Date();
        const newCurrentTime = new Date(`2025-01-01 ${newNow.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`);
        const newDiffMinutes = Math.max(0, Math.floor((newCurrentTime - startTime) / 60000));
        setWaitingTime(newDiffMinutes);
      }, 60000);
      
      return () => clearInterval(interval);
    }
  }, [sectionType, appointment.heure]);

  const getWhatsAppLink = (numero) => {
    if (!numero) return '#';
    const cleanNumber = numero.replace(/\D/g, '');
    return `https://wa.me/${cleanNumber}`;
  };

  const handleStatusChange = (newStatus) => {
    onStatusUpdate(appointment.id, newStatus);
    setShowStatusDropdown(false);
  };

  const handleRoomChange = (room) => {
    onRoomAssignment(appointment.id, room);
    setShowRoomDropdown(false);
  };

  const getPaymentStatus = () => {
    // Si c'est un contrôle, toujours gratuit
    if (appointment.type_rdv === 'controle') {
      return { status: 'gratuit', text: 'Gratuit', color: 'bg-green-100 text-green-800 font-bold' };
    }
    
    // Pour les visites
    if (appointment.paye) {
      return { status: 'paye', text: 'Payé', color: 'bg-green-100 text-green-800 font-bold' };
    }
    
    // Par défaut : Non payé en rouge gras
    return { status: 'non_paye', text: 'Non payé', color: 'bg-red-100 text-red-800 font-bold' };
  };

  const paymentStatus = getPaymentStatus();

  return (
    <div className="p-4 hover:bg-white/50 transition-colors">
      <div className="flex items-center justify-between">
        {/* Partie gauche - Info patient */}
        <div className="flex items-center space-x-4 flex-1">
          {/* Heure */}
          <div className="flex items-center space-x-2 min-w-0">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">{appointment.heure}</span>
          </div>

          {/* Nom patient cliquable */}
          <div className="flex-1 min-w-0">
            <button
              onClick={() => onViewPatient(appointment.patient_id)}
              className="font-semibold text-gray-900 hover:text-primary-600 transition-colors cursor-pointer underline text-left"
            >
              {appointment.patient?.prenom} {appointment.patient?.nom}
            </button>
            
            {/* Compteur durée d'attente pour patients en attente */}
            {sectionType === 'attente' && (
              <div className="text-xs text-orange-600 font-medium mt-1">
                ⏱️ En attente depuis {waitingTime} min
              </div>
            )}
          </div>
        </div>

        {/* Badges interactifs */}
        <div className="flex items-center space-x-2">
          {/* Badge C/V - Cliquable pour basculer */}
          <button
            onClick={() => onTypeToggle(appointment.id, appointment.type_rdv)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors cursor-pointer hover:opacity-80 ${
              appointment.type_rdv === 'visite' 
                ? 'bg-blue-100 text-blue-800 hover:bg-blue-200' 
                : 'bg-green-100 text-green-800 hover:bg-green-200'
            }`}
            title={`Cliquer pour changer vers ${appointment.type_rdv === 'visite' ? 'Contrôle' : 'Visite'}`}
          >
            {appointment.type_rdv === 'visite' ? 'V' : 'C'}
          </button>

          {/* Badge Statut - Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowStatusDropdown(!showStatusDropdown)}
              className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200 transition-colors cursor-pointer"
              title="Cliquer pour changer le statut"
            >
              {appointment.statut}
            </button>
            
            {showStatusDropdown && (
              <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[120px]">
                {['attente', 'en_cours', 'termine', 'absent'].map(status => (
                  <button
                    key={status}
                    onClick={() => handleStatusChange(status)}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors"
                  >
                    {status}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Badge Salle - Apparaît seulement si en attente */}
          {sectionType === 'attente' && (
            <div className="relative">
              <button
                onClick={() => setShowRoomDropdown(!showRoomDropdown)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                  appointment.salle 
                    ? 'bg-purple-100 text-purple-800 hover:bg-purple-200' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title="Affecter à une salle"
              >
                {appointment.salle === 'salle1' ? 'S1' : appointment.salle === 'salle2' ? 'S2' : 'Salle?'}
              </button>
              
              {showRoomDropdown && (
                <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[100px]">
                  <button
                    onClick={() => handleRoomChange('salle1')}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors"
                  >
                    Salle 1
                  </button>
                  <button
                    onClick={() => handleRoomChange('salle2')}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors"
                  >
                    Salle 2
                  </button>
                  <button
                    onClick={() => handleRoomChange('')}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors text-gray-500"
                  >
                    Aucune
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Badge Paiement - Cliquable pour modal */}
          <button
            onClick={() => setShowPaymentModal(true)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors cursor-pointer hover:opacity-80 ${paymentStatus.color}`}
            title="Cliquer pour gérer le paiement"
          >
            {paymentStatus.text}
          </button>

          {/* Bouton ENTRER pour patients en attente */}
          {sectionType === 'attente' && (
            <button
              onClick={() => onStartConsultation(appointment.id)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded font-medium transition-colors"
              title="Démarrer la consultation"
            >
              ENTRER
            </button>
          )}

          {/* Bouton WhatsApp */}
          <a
            href={getWhatsAppLink(appointment.patient?.numero_whatsapp || appointment.patient?.telephone)}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
            title="Envoyer WhatsApp"
          >
            <MessageCircle className="w-4 h-4" />
          </a>

          {/* Bouton Edit */}
          <button
            onClick={() => onEdit(appointment)}
            className="p-1 text-blue-600 hover:bg-blue-100 rounded transition-colors"
            title="Modifier"
          >
            <Edit className="w-4 h-4" />
          </button>

          {/* Bouton Supprimer */}
          <button
            onClick={() => onDelete(appointment.id)}
            className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
            title="Supprimer"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Modal Paiement */}
      {showPaymentModal && (
        <PaymentModal
          appointment={appointment}
          onClose={() => setShowPaymentModal(false)}
          onUpdate={onPaymentUpdate}
        />
      )}
    </div>
  );
};

// Modal de paiement
const PaymentModal = ({ appointment, onClose, onUpdate }) => {
  const [paymentData, setPaymentData] = useState({
    paye: appointment.paye || false,
    montant: appointment.type_rdv === 'visite' ? 300 : 0,
    gratuit: appointment.type_rdv === 'controle',
    assure: false,
    methode_paiement: 'espece'
  });

  const handleSubmit = () => {
    onUpdate(appointment.id, paymentData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Gestion Paiement</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Patient: {appointment.patient?.prenom} {appointment.patient?.nom}
            </label>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                checked={paymentData.paye}
                onChange={() => setPaymentData(prev => ({ ...prev, paye: true, gratuit: false }))}
                className="mr-2"
              />
              Payé
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                checked={!paymentData.paye && !paymentData.gratuit}
                onChange={() => setPaymentData(prev => ({ ...prev, paye: false, gratuit: false }))}
                className="mr-2"
              />
              Non payé
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                checked={paymentData.gratuit}
                onChange={() => setPaymentData(prev => ({ ...prev, gratuit: true, paye: false }))}
                className="mr-2"
              />
              Gratuit
            </label>
          </div>

          {paymentData.paye && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Montant (TND)
                </label>
                <input
                  type="number"
                  value={paymentData.montant}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, montant: parseInt(e.target.value) }))}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Méthode de paiement
                </label>
                <select
                  value={paymentData.methode_paiement}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, methode_paiement: e.target.value }))}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                >
                  <option value="espece">Espèces</option>
                  <option value="carte">Carte bancaire</option>
                  <option value="cheque">Chèque</option>
                </select>
              </div>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={paymentData.assure}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, assure: e.target.checked }))}
                  className="mr-2"
                />
                Patient assuré
              </label>
            </>
          )}
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded transition-colors"
          >
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
};
export default Calendar;