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
  CheckCircle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

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
      programme: [],
      attente: [],
      en_cours: [],
      retard: [],
      absent: [],
      termine: []
    };
    
    sortedAppointments.forEach(apt => {
      if (groups[apt.statut]) {
        groups[apt.statut].push(apt);
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

      {/* List View */}
      {viewMode === 'list' && (
        <div className="space-y-6">
          {/* À venir (Bleu) */}
          {groupedAppointments.programme.length > 0 && (
            <AppointmentSection
              title="À venir"
              appointments={groupedAppointments.programme}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onPatientArrival={handlePatientArrival}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
            />
          )}
          
          {/* En salle d'attente (Vert) */}
          {groupedAppointments.attente.length > 0 && (
            <AppointmentSection
              title="En salle d'attente"
              appointments={groupedAppointments.attente}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
            />
          )}
          
          {/* En cours (Jaune) */}
          {groupedAppointments.en_cours.length > 0 && (
            <AppointmentSection
              title="En cours"
              appointments={groupedAppointments.en_cours}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
            />
          )}
          
          {/* En retard (Orange) */}
          {groupedAppointments.retard.length > 0 && (
            <AppointmentSection
              title="En retard"
              appointments={groupedAppointments.retard}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
            />
          )}
          
          {/* Absents (Rouge) */}
          {groupedAppointments.absent.length > 0 && (
            <AppointmentSection
              title="Absents"
              appointments={groupedAppointments.absent}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
            />
          )}
          
          {/* Terminés (Gris, en bas) */}
          {groupedAppointments.termine.length > 0 && (
            <AppointmentSection
              title="Terminés"
              appointments={groupedAppointments.termine}
              onStatusUpdate={handleStatusUpdate}
              onRoomAssignment={handleRoomAssignment}
              onEdit={openModal}
              onDelete={handleDeleteAppointment}
              onViewPatient={viewPatientDetails}
              isCompleted
            />
          )}
          
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

// Composant pour les sections d'appointments
const AppointmentSection = ({ 
  title, 
  appointments, 
  onStatusUpdate, 
  onRoomAssignment,
  onPatientArrival,
  onEdit, 
  onDelete, 
  onViewPatient,
  isCompleted = false 
}) => {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 ${isCompleted ? 'opacity-75' : ''}`}>
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600">{appointments.length} rendez-vous</p>
      </div>
      
      <div className="divide-y divide-gray-100">
        {appointments.map((appointment) => (
          <AppointmentCard
            key={appointment.id}
            appointment={appointment}
            onStatusUpdate={onStatusUpdate}
            onRoomAssignment={onRoomAssignment}
            onEdit={onEdit}
            onDelete={onDelete}
            onViewPatient={onViewPatient}
            isCompleted={isCompleted}
          />
        ))}
      </div>
    </div>
  );
};

// Composant pour une carte de rendez-vous
const AppointmentCard = ({ 
  appointment, 
  onStatusUpdate, 
  onRoomAssignment, 
  onEdit, 
  onDelete, 
  onViewPatient,
  isCompleted 
}) => {
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

  const getWhatsAppLink = (numero) => {
    if (!numero) return '#';
    const cleanNumber = numero.replace(/\D/g, '');
    return `https://wa.me/${cleanNumber}`;
  };

  const cycleStatus = () => {
    const statusCycle = {
      'programme': 'attente',
      'attente': 'en_cours', 
      'en_cours': 'termine',
      'termine': 'programme',
      'absent': 'programme',
      'retard': 'attente'
    };
    onStatusUpdate(appointment.id, statusCycle[appointment.statut] || 'programme');
  };

  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          {/* Time */}
          <div className="flex items-center space-x-2 min-w-0">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="font-semibold text-gray-900">{appointment.heure}</span>
          </div>
          
          {/* Patient Info */}
          <div className="flex-1 min-w-0">
            <button
              onClick={() => onViewPatient(appointment.patient_id)}
              className="font-medium text-gray-900 hover:text-primary-600 transition-colors cursor-pointer underline"
            >
              {appointment.patient?.prenom} {appointment.patient?.nom}
            </button>
            <div className="text-sm text-gray-500 truncate">
              {appointment.motif || 'Consultation'}
            </div>
          </div>
          
          {/* Badges */}
          <div className="flex items-center space-x-2">
            {/* Type Badge */}
            <span className={`px-2 py-1 rounded text-xs font-medium border ${
              appointment.type_rdv === 'visite' 
                ? 'bg-blue-50 text-blue-700 border-blue-200' 
                : 'bg-green-50 text-green-700 border-green-200'
            }`}>
              {appointment.type_rdv === 'visite' ? 'V' : 'C'}
            </span>
            
            {/* Status Badge - Clickable */}
            <button
              onClick={cycleStatus}
              className={`px-2 py-1 rounded text-xs font-medium border transition-all hover:shadow-sm ${getStatusColor(appointment.statut)}`}
            >
              {appointment.statut === 'programme' ? 'Programmé' :
               appointment.statut === 'attente' ? 'Attente' :
               appointment.statut === 'en_cours' ? 'En cours' :
               appointment.statut === 'termine' ? 'Terminé' :
               appointment.statut === 'absent' ? 'Absent' :
               appointment.statut === 'retard' ? 'Retard' : 'Programmé'}
            </button>
            
            {/* Payment Badge */}
            <span className={`px-2 py-1 rounded text-xs font-medium border ${
              appointment.paye 
                ? 'bg-green-50 text-green-700 border-green-200' 
                : 'bg-red-50 text-red-700 border-red-200'
            }`}>
              {appointment.paye ? 'Payé' : 'Non payé'}
            </span>
            
            {/* Room Badge */}
            {appointment.salle && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                {appointment.salle === 'salle1' ? 'Salle 1' : 'Salle 2'}
              </span>
            )}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center space-x-2 ml-4">
          {/* WhatsApp */}
          {appointment.patient?.lien_whatsapp && (
            <a
              href={appointment.patient.lien_whatsapp}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              title="WhatsApp"
            >
              <MessageCircle className="w-4 h-4" />
            </a>
          )}
          
          {/* Room Assignment */}
          {!isCompleted && (
            <div className="flex space-x-1">
              <button
                onClick={() => {
                  // Si le patient n'est pas encore arrivé, le marquer comme arrivé
                  if (appointment.statut === 'programme') {
                    onPatientArrival(appointment.id, 'salle1');
                  } else {
                    onRoomAssignment(appointment.id, 'salle1');
                  }
                }}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  appointment.salle === 'salle1' 
                    ? 'bg-purple-100 text-purple-800' 
                    : 'bg-gray-100 text-gray-600 hover:bg-purple-50'
                }`}
                title={appointment.statut === 'programme' ? 'Patient arrivé → Salle 1' : 'Affecter à Salle 1'}
              >
                {appointment.statut === 'programme' ? '🚪→S1' : 'S1'}
              </button>
              <button
                onClick={() => {
                  // Si le patient n'est pas encore arrivé, le marquer comme arrivé
                  if (appointment.statut === 'programme') {
                    onPatientArrival(appointment.id, 'salle2');
                  } else {
                    onRoomAssignment(appointment.id, 'salle2');
                  }
                }}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  appointment.salle === 'salle2' 
                    ? 'bg-purple-100 text-purple-800' 
                    : 'bg-gray-100 text-gray-600 hover:bg-purple-50'
                }`}
                title={appointment.statut === 'programme' ? 'Patient arrivé → Salle 2' : 'Affecter à Salle 2'}
              >
                {appointment.statut === 'programme' ? '🚪→S2' : 'S2'}
              </button>
            </div>
          )}
          
          {/* Edit */}
          <button
            onClick={() => onEdit(appointment)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Modifier"
          >
            <Edit className="w-4 h-4" />
          </button>
          
          {/* Delete */}
          <button
            onClick={() => onDelete(appointment.id)}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Supprimer"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Modal de rendez-vous
const AppointmentModal = ({ 
  isOpen, 
  onClose, 
  appointment, 
  patients, 
  formData, 
  setFormData, 
  onSave, 
  onRefresh,
  onOpenPatientModal 
}) => {
  const [isNewPatient, setIsNewPatient] = useState(false);
  const [patientSearch, setPatientSearch] = useState('');
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [newPatientData, setNewPatientData] = useState({
    nom: '',
    prenom: '',
    telephone: ''
  });

  useEffect(() => {
    if (isOpen && appointment) {
      // Si on modifie un appointment existant, trouver le nom du patient
      const patient = patients.find(p => p.id === appointment.patient_id);
      if (patient) {
        setPatientSearch(`${patient.prenom} ${patient.nom}`);
        setIsNewPatient(false);
      }
    } else if (isOpen) {
      // Nouveau RDV
      setPatientSearch('');
      setIsNewPatient(false);
      setNewPatientData({ nom: '', prenom: '', telephone: '' });
    }
  }, [isOpen, appointment, patients]);

  useEffect(() => {
    if (patientSearch && !isNewPatient) {
      const filtered = patients.filter(patient =>
        `${patient.prenom} ${patient.nom}`.toLowerCase().includes(patientSearch.toLowerCase()) ||
        `${patient.nom} ${patient.prenom}`.toLowerCase().includes(patientSearch.toLowerCase())
      );
      setFilteredPatients(filtered);
      setShowSuggestions(filtered.length > 0 && patientSearch.length > 1);
    } else {
      setFilteredPatients([]);
      setShowSuggestions(false);
    }
  }, [patientSearch, patients, isNewPatient]);

  const handlePatientSelect = (patient) => {
    setPatientSearch(`${patient.prenom} ${patient.nom}`);
    setFormData({ ...formData, patient_id: patient.id });
    setShowSuggestions(false);
  };

  const handleNewPatientToggle = (checked) => {
    setIsNewPatient(checked);
    if (checked) {
      setPatientSearch('');
      setFormData({ ...formData, patient_id: '' });
      setShowSuggestions(false);
    } else {
      setNewPatientData({ nom: '', prenom: '', telephone: '' });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isNewPatient) {
      // Validation des champs requis
      if (!newPatientData.nom || !newPatientData.prenom || !newPatientData.telephone) {
        toast.error('Veuillez remplir tous les champs du nouveau patient');
        return;
      }
      
      // Créer d'abord le nouveau patient
      try {
        // Générer un UUID simple pour le nouveau patient
        const patientId = 'patient_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        const patientData = {
          id: patientId,
          nom: newPatientData.nom,
          prenom: newPatientData.prenom,
          telephone: newPatientData.telephone,
          date_naissance: '',
          adresse: '',
          pere: { nom: '', telephone: '', fonction: '' },
          mere: { nom: '', telephone: '', fonction: '' },
          numero_whatsapp: newPatientData.telephone,
          notes: '',
          antecedents: '',
          consultations: []
        };
        
        const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';
        
        // Créer le patient
        const patientResponse = await axios.post(`${API_BASE_URL}/api/patients`, patientData);
        console.log('Patient créé:', patientResponse.data);
        
        // Créer le RDV avec le nouveau patient
        const updatedFormData = { 
          ...formData, 
          patient_id: patientId
        };
        
        const appointmentResponse = await axios.post(`${API_BASE_URL}/api/appointments`, updatedFormData);
        console.log('RDV créé:', appointmentResponse.data);
        
        toast.success('Patient et rendez-vous créés avec succès');
        onClose();
        // Rafraîchir les données du calendrier
        if (onRefresh) {
          await onRefresh();
        }
        
      } catch (error) {
        console.error('Error creating patient and appointment:', error);
        console.error('Error details:', error.response?.data);
        toast.error('Erreur lors de la création: ' + (error.response?.data?.detail || error.message));
      }
    } else {
      // Validation pour patient existant
      if (!formData.patient_id) {
        toast.error('Veuillez sélectionner un patient');
        return;
      }
      
      // RDV normal
      onSave();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {appointment ? 'Modifier le rendez-vous' : 'Nouveau rendez-vous'}
          </h2>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* Case Nouveau Patient */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="newPatient"
                  checked={isNewPatient}
                  onChange={(e) => handleNewPatientToggle(e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="newPatient" className="ml-2 text-sm font-medium text-gray-700">
                  Nouveau patient
                </label>
              </div>

              {/* Patient Selection ou Nouveau Patient */}
              {!isNewPatient ? (
                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                  <input
                    type="text"
                    value={patientSearch}
                    onChange={(e) => setPatientSearch(e.target.value)}
                    onFocus={() => setShowSuggestions(filteredPatients.length > 0)}
                    className="input-field"
                    placeholder="Tapez le nom du patient..."
                    required={!isNewPatient}
                  />
                  
                  {/* Suggestions dropdown */}
                  {showSuggestions && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                      {filteredPatients.map((patient) => (
                        <button
                          key={patient.id}
                          type="button"
                          onClick={() => handlePatientSelect(patient)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
                        >
                          <div className="font-medium text-gray-900">
                            {patient.prenom} {patient.nom}
                          </div>
                          <div className="text-sm text-gray-500">
                            {patient.telephone} {patient.date_naissance && `• ${patient.date_naissance}`}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                /* Champs Nouveau Patient */
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <h3 className="text-sm font-medium text-blue-900 mb-3">Informations du nouveau patient</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                      <input
                        type="text"
                        value={newPatientData.nom}
                        onChange={(e) => setNewPatientData({...newPatientData, nom: e.target.value})}
                        className="input-field"
                        required={isNewPatient}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                      <input
                        type="text"
                        value={newPatientData.prenom}
                        onChange={(e) => setNewPatientData({...newPatientData, prenom: e.target.value})}
                        className="input-field"
                        required={isNewPatient}
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                    <input
                      type="tel"
                      value={newPatientData.telephone}
                      onChange={(e) => setNewPatientData({...newPatientData, telephone: e.target.value})}
                      className="input-field"
                      placeholder="216xxxxxxxx"
                      required={isNewPatient}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Heure</label>
                <input
                  type="time"
                  value={formData.heure}
                  onChange={(e) => setFormData({...formData, heure: e.target.value})}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type de RDV</label>
                <select
                  value={formData.type_rdv}
                  onChange={(e) => setFormData({...formData, type_rdv: e.target.value})}
                  className="input-field"
                >
                  <option value="visite">Visite payante</option>
                  <option value="controle">Contrôle gratuit</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Motif</label>
                <input
                  type="text"
                  value={formData.motif}
                  onChange={(e) => setFormData({...formData, motif: e.target.value})}
                  className="input-field"
                  placeholder="Motif de la consultation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="input-field"
                  rows="3"
                  placeholder="Notes supplémentaires"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="btn-outline"
              >
                Annuler
              </button>
              <button
                type="submit"
                className="btn-primary"
              >
                {appointment ? 'Modifier' : 'Créer'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Calendar;