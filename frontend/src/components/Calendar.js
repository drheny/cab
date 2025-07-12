import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Calendar as CalendarIcon, 
  Plus, 
  Edit, 
  Trash2, 
  Clock, 
  User,
  Phone,
  MessageCircle,
  ChevronLeft,
  ChevronRight,
  MapPin,
  BarChart3,
  List,
  Grid,
  CheckCircle,
  XCircle,
  Pause,
  AlertCircle,
  UserPlus
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
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [weekData, setWeekData] = useState({ week_dates: [], appointments: [] });
  
  // Form states
  const [formData, setFormData] = useState({
    patient_id: '',
    date: '',
    heure: '',
    type_rdv: 'visite',
    motif: '',
    notes: ''
  });
  
  const [newPatientData, setNewPatientData] = useState({
    nom: '',
    prenom: '',
    telephone: ''
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchData();
    
    // Auto-open modal from Dashboard quick action
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('action') === 'add') {
      openModal();
      window.history.replaceState({}, '', '/calendar');
    }
  }, [selectedDate, viewMode]);

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
      await axios.post('/api/appointments', formData);
      toast.success('Rendez-vous créé avec succès');
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Error creating appointment:', error);
      toast.error('Erreur lors de la création du rendez-vous');
    }
  };

  const handleUpdateAppointment = async () => {
    try {
      await axios.put(`/api/appointments/${selectedAppointment.id}`, formData);
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
        await axios.delete(`/api/appointments/${appointmentId}`);
        toast.success('Rendez-vous supprimé avec succès');
        fetchData();
      } catch (error) {
        console.error('Error deleting appointment:', error);
        toast.error('Erreur lors de la suppression du rendez-vous');
      }
    }
  };

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
        motif: appointment.motif,
        notes: appointment.notes
      });
    } else {
      resetForm();
    }
    setShowModal(true);
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
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Nouveau RDV</span>
        </button>
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

      {/* Appointments List - PC Optimized Table */}
      <div className="pc-table-container">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Rendez-vous du {formatDate(selectedDate)}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {appointments.length} rendez-vous programmés
          </p>
        </div>

        <div className="overflow-x-auto">
          {appointments.length === 0 ? (
            <div className="text-center py-8">
              <CalendarIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun rendez-vous pour cette date</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Heure</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Salle</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motif</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {appointments.sort((a, b) => a.heure.localeCompare(b.heure)).map((appointment) => (
                  <tr key={appointment.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900 text-sm">{appointment.heure}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div>
                        <div className="font-medium text-gray-900 text-sm">
                          {appointment.patient?.prenom} {appointment.patient?.nom}
                        </div>
                        <div className="text-xs text-gray-500">
                          ({appointment.patient?.nom_parent})
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        appointment.type_rdv === 'visite' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {appointment.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.statut)}`}>
                        {getStatusText(appointment.statut)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {appointment.salle && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                          {appointment.salle === 'salle1' ? 'Salle 1' : 'Salle 2'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 max-w-xs truncate text-sm text-gray-600">
                      {appointment.motif || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center space-x-1">
                        {appointment.patient?.telephone_parent && (
                          <a
                            href={getWhatsAppLink(appointment.patient.telephone_parent)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          >
                            <MessageCircle className="w-4 h-4" />
                          </a>
                        )}
                        <button
                          onClick={() => openModal(appointment)}
                          className="p-1.5 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteAppointment(appointment.id)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                {selectedAppointment ? 'Modifier le rendez-vous' : 'Nouveau rendez-vous'}
              </h2>

              <form onSubmit={(e) => {
                e.preventDefault();
                selectedAppointment ? handleUpdateAppointment() : handleCreateAppointment();
              }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                    <select
                      value={formData.patient_id}
                      onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                      className="input-field"
                      required
                    >
                      <option value="">Sélectionner un patient</option>
                      {patients.map((patient) => (
                        <option key={patient.id} value={patient.id}>
                          {patient.prenom} {patient.nom} ({patient.nom_parent})
                        </option>
                      ))}
                    </select>
                  </div>

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
                    onClick={() => setShowModal(false)}
                    className="btn-outline"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    {selectedAppointment ? 'Modifier' : 'Créer'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar;