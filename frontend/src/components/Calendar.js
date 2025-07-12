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
      await axios.post(`${API_BASE_URL}/api/appointments`, formData);
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

  const handleCreatePatientExpress = async () => {
    try {
      const patientData = {
        id: Date.now().toString(),
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
      
      await axios.post(`${API_BASE_URL}/api/patients`, patientData);
      
      // Update form with new patient
      setFormData({ ...formData, patient_id: patientData.id });
      setShowPatientModal(false);
      setNewPatientData({ nom: '', prenom: '', telephone: '' });
      
      // Refresh patients list
      const patientsRes = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(patientsRes.data.patients || []);
      
      toast.success('Patient créé avec succès');
    } catch (error) {
      console.error('Error creating patient:', error);
      toast.error('Erreur lors de la création du patient');
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

      {/* Week View */}
      {viewMode === 'week' && (
        <WeekView
          weekData={weekData}
          onStatusUpdate={handleStatusUpdate}
          onRoomAssignment={handleRoomAssignment}
          onEdit={openModal}
          onDelete={handleDeleteAppointment}
          selectedDate={selectedDate}
        />
      )}

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

// Composant WeekView pour la vue semaine
const WeekView = ({ weekData, onStatusUpdate, onRoomAssignment, onEdit, onDelete, selectedDate }) => {
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

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Vue Semaine</h3>
        <p className="text-sm text-gray-600">Lundi → Samedi • 9h00 → 18h00</p>
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
              <div key={time} className="grid grid-cols-7 border-b border-gray-100 hover:bg-gray-50">
                {/* Time column */}
                <div className="p-2 border-r border-gray-200 bg-gray-50">
                  <span className="text-xs text-gray-600 font-mono">{time}</span>
                </div>
                
                {/* Days columns */}
                {weekData.week_dates?.map((date) => {
                  const appointments = getAppointmentsForDateAndTime(date, time);
                  return (
                    <div key={`${date}-${time}`} className="p-1 border-r border-gray-100 last:border-r-0 min-h-[50px]">
                      {appointments.map((apt) => (
                        <div
                          key={apt.id}
                          className={`text-xs p-1 rounded mb-1 border cursor-pointer hover:shadow-sm transition-all ${getStatusColor(apt.statut)}`}
                          onClick={() => onEdit(apt)}
                          title={`${apt.patient?.prenom} ${apt.patient?.nom} - ${apt.motif || 'Consultation'}`}
                        >
                          <div className="truncate">
                            <span className="font-medium">{apt.patient?.prenom} {apt.patient?.nom}</span>
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
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Week Summary */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-600">
            Total rendez-vous de la semaine: <span className="font-medium">{weekData.appointments?.length || 0}</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-blue-100 border border-blue-200"></div>
              <span className="text-gray-600">Programmé</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-green-100 border border-green-200"></div>
              <span className="text-gray-600">Attente</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-yellow-100 border border-yellow-200"></div>
              <span className="text-gray-600">En cours</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded bg-gray-100 border border-gray-200"></div>
              <span className="text-gray-600">Terminé</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Calendar;