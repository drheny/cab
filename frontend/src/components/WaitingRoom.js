import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Users, 
  CheckCircle,
  ArrowRight,
  Trash2,
  AlertCircle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const WaitingRoom = ({ user }) => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [salle1, setSalle1] = useState([]);
  const [salle2, setSalle2] = useState([]);
  const [stats, setStats] = useState({
    salle1Count: 0,
    salle2Count: 0,
    enCoursCount: 0,
    totalPatients: 0
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchTodayAppointments();
    // Refresh every 30 seconds
    const interval = setInterval(fetchTodayAppointments, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTodayAppointments = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API_BASE_URL}/api/rdv/jour/${today}`);
      
      const appointmentsData = response.data.rdv || response.data || [];
      setAppointments(appointmentsData);
      
      // Filter patients by room (only waiting or in consultation)
      const salle1Patients = appointmentsData.filter(apt => 
        apt.salle === 'salle1' && ['attente', 'en_cours'].includes(apt.statut)
      );
      const salle2Patients = appointmentsData.filter(apt => 
        apt.salle === 'salle2' && ['attente', 'en_cours'].includes(apt.statut)
      );
      
      setSalle1(salle1Patients);
      setSalle2(salle2Patients);
      
      // Calculate basic stats
      const stats = {
        salle1Count: salle1Patients.length,
        salle2Count: salle2Patients.length,
        enCoursCount: appointmentsData.filter(apt => apt.statut === 'en_cours').length,
        totalPatients: salle1Patients.length + salle2Patients.length
      };
      
      setStats(stats);
      
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Erreur lors du chargement des rendez-vous');
    } finally {
      setLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId, newStatus) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, {
        statut: newStatus
      });
      toast.success('Statut mis à jour avec succès');
      fetchTodayAppointments();
    } catch (error) {
      console.error('Error updating appointment:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const startConsultation = (appointmentId) => {
    updateAppointmentStatus(appointmentId, 'en_cours');
  };

  const finishConsultation = (appointmentId) => {
    updateAppointmentStatus(appointmentId, 'termine');
  };

  const markAsAbsent = (appointmentId) => {
    updateAppointmentStatus(appointmentId, 'absent');
  };

  // Simple waiting time calculation (15 min per patient ahead)
  const calculateWaitingTime = (patients, currentPatientId) => {
    const currentIndex = patients.findIndex(p => p.id === currentPatientId);
    if (currentIndex === -1) return { minutes: 0, position: 0 };
    
    const patientsAhead = patients.slice(0, currentIndex).filter(p => p.statut === 'attente');
    const estimatedMinutes = patientsAhead.length * 15;
    
    return {
      minutes: estimatedMinutes,
      position: currentIndex + 1
    };
  };

  const PatientCard = ({ 
    appointment, 
    patients, 
    onStart, 
    onFinish, 
    onMarkAbsent, 
    index 
  }) => {
    const waitingTime = calculateWaitingTime(patients, appointment.id);
    
    const getStatusColor = (status) => {
      switch (status) {
        case 'attente': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        case 'en_cours': return 'bg-blue-100 text-blue-800 border-blue-200';
        case 'termine': return 'bg-green-100 text-green-800 border-green-200';
        default: return 'bg-gray-100 text-gray-800 border-gray-200';
      }
    };

    const getStatusIcon = (status) => {
      switch (status) {
        case 'attente': return <Clock className="w-4 h-4" />;
        case 'en_cours': return <Users className="w-4 h-4" />;
        case 'termine': return <CheckCircle className="w-4 h-4" />;
        default: return <AlertCircle className="w-4 h-4" />;
      }
    };

    return (
      <div className={`p-4 rounded-lg border-2 ${getStatusColor(appointment.statut)} mb-3 shadow-sm`}>
        {/* Patient Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex-1">
            <h3 className="font-semibold text-lg">
              {appointment.patient?.prenom} {appointment.patient?.nom}
            </h3>
            <div className="flex items-center space-x-4 text-sm opacity-75 mt-1">
              <span>📅 {appointment.heure}</span>
              <span className={`px-2 py-1 rounded ${
                appointment.type_rdv === 'visite' 
                  ? 'bg-yellow-200 text-yellow-800' 
                  : 'bg-green-200 text-green-800'
              }`}>
                {appointment.type_rdv === 'visite' ? '💰 Visite' : '🆓 Contrôle'}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs font-medium">
              #{index + 1}
            </span>
            {getStatusIcon(appointment.statut)}
            <span className="text-sm font-medium capitalize">{appointment.statut}</span>
          </div>
        </div>

        {/* Simple waiting time display */}
        {appointment.statut === 'attente' && (
          <div className="bg-white bg-opacity-50 p-3 rounded mb-3 border-l-4 border-blue-400">
            <div className="flex justify-between text-sm">
              <div>
                <span className="font-medium text-gray-700">⏱️ Temps estimé:</span>
                <div className="text-lg font-bold text-blue-600">~{waitingTime.minutes} min</div>
              </div>
              <div>
                <span className="font-medium text-gray-700">👥 Position:</span>
                <div className="text-lg font-bold text-gray-600">#{waitingTime.position}</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex space-x-2">
          {appointment.statut === 'attente' && (
            <button
              onClick={() => onStart(appointment.id)}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded transition-colors flex items-center justify-center space-x-1"
              title="Commencer la consultation"
            >
              <Users className="w-4 h-4" />
              <span>Démarrer consultation</span>
            </button>
          )}
          
          {appointment.statut === 'en_cours' && (
            <button
              onClick={() => onFinish(appointment.id)}
              className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded transition-colors flex items-center justify-center space-x-1"
              title="Terminer la consultation"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Terminer consultation</span>
            </button>
          )}
          
          {appointment.statut === 'termine' && (
            <div className="flex-1 bg-gray-100 text-gray-600 text-sm py-2 px-3 rounded flex items-center justify-center space-x-1">
              <CheckCircle className="w-4 h-4" />
              <span>Consultation terminée</span>
            </div>
          )}
          
          <button
            onClick={() => onMarkAbsent(appointment.id)}
            className="p-2 text-red-500 hover:bg-red-100 rounded transition-colors"
            title="Marquer comme absent"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  const SalleColumn = ({ 
    title, 
    patients, 
    color, 
    onStart, 
    onFinish, 
    onMarkAbsent 
  }) => {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <span className={`bg-${color}-100 text-${color}-800 px-3 py-1 rounded-full text-sm font-medium`}>
            {patients.length} patient(s)
          </span>
        </div>
        
        <div className="space-y-3 min-h-32">
          {patients.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Aucun patient en attente</p>
            </div>
          ) : (
            patients.map((appointment, index) => (
              <PatientCard
                key={appointment.id}
                appointment={appointment}
                patients={patients}
                onStart={onStart}
                onFinish={onFinish}
                onMarkAbsent={onMarkAbsent}
                index={index}
              />
            ))
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Adaptive layout: if Salle 2 is empty, Salle 1 takes full width
  const isSalle2Empty = salle2.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Salles d'attente</h1>
          <p className="text-gray-600">Gestion simple des patients en attente</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Dernière mise à jour</div>
          <div className="text-sm font-medium">{new Date().toLocaleTimeString()}</div>
        </div>
      </div>

      {/* Simple stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-500" />
            <span className="text-sm font-medium">Salle 1</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{stats.salle1Count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium">Salle 2</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{stats.salle2Count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-yellow-500" />
            <span className="text-sm font-medium">En cours</span>
          </div>
          <p className="text-2xl font-bold text-yellow-600">{stats.enCoursCount}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-purple-500" />
            <span className="text-sm font-medium">Total patients</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">{stats.totalPatients}</p>
        </div>
      </div>

      {/* Rooms - Adaptive layout */}
      <div className={`grid ${isSalle2Empty ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'} gap-6 transition-all duration-300`}>
        {/* Salle 1 - Always visible */}
        <SalleColumn
          title="Salle 1"
          patients={salle1}
          color="blue"
          onStart={startConsultation}
          onFinish={finishConsultation}
          onMarkAbsent={markAsAbsent}
        />

        {/* Salle 2 - Only visible if it has patients */}
        {!isSalle2Empty && (
          <SalleColumn
            title="Salle 2"
            patients={salle2}
            color="green"
            onStart={startConsultation}
            onFinish={finishConsultation}
            onMarkAbsent={markAsAbsent}
          />
        )}
      </div>
    </div>
  );
};

export default WaitingRoom;