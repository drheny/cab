import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { 
  Clock, 
  Users, 
  DollarSign, 
  CheckCircle, 
  ArrowRight,
  Plus,
  Trash2,
  AlertCircle,
  Phone,
  CreditCard,
  Calendar,
  GripVertical
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
    termineCount: 0,
    totalRecettes: 0
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchTodayAppointments();
    // Rafraîchir les données toutes les 30 secondes
    const interval = setInterval(fetchTodayAppointments, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTodayAppointments = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API_BASE_URL}/api/rdv/jour/${today}`);
      const appointmentsData = response.data.rdv || [];
      
      setAppointments(appointmentsData);
      
      // Séparer les patients par salle (seulement ceux en attente ou en consultation)
      const salle1Patients = appointmentsData.filter(apt => 
        apt.salle === 'salle1' && ['attente', 'en_cours'].includes(apt.statut)
      );
      const salle2Patients = appointmentsData.filter(apt => 
        apt.salle === 'salle2' && ['attente', 'en_cours'].includes(apt.statut)
      );
      
      setSalle1(salle1Patients);
      setSalle2(salle2Patients);
      
      // Calculer les statistiques
      const stats = {
        salle1Count: salle1Patients.length,
        salle2Count: salle2Patients.length,
        enCoursCount: appointmentsData.filter(apt => apt.statut === 'en_cours').length,
        termineCount: appointmentsData.filter(apt => apt.statut === 'termine').length,
        totalRecettes: appointmentsData
          .filter(apt => apt.paye && apt.type_rdv === 'visite')
          .reduce((sum, apt) => sum + 300, 0)
      };
      
      setStats(stats);
      
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Erreur lors du chargement des rendez-vous');
    } finally {
      setLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId, newStatus, salle = '') => {
    try {
      const appointment = appointments.find(apt => apt.id === appointmentId);
      if (!appointment) return;

      const updateData = {
        statut: newStatus,
        ...(salle && { salle })
      };

      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, updateData);
      toast.success('Statut mis à jour avec succès');
      fetchTodayAppointments();
    } catch (error) {
      console.error('Error updating appointment:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const updateAppointmentRoom = async (appointmentId, targetSalle) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/salle`, {
        salle: targetSalle
      });
      toast.success(`Patient déplacé vers ${targetSalle}`);
      fetchTodayAppointments();
    } catch (error) {
      console.error('Error updating room:', error);
      toast.error('Erreur lors du déplacement');
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

  // **PHASE 2: Drag & Drop Logic**
  const handleDragEnd = async (result) => {
    const { destination, source, draggableId } = result;

    // Pas de destination = drag annulé
    if (!destination) {
      return;
    }

    // Pas de changement
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }

    try {
      // Déplacement entre salles
      if (source.droppableId !== destination.droppableId) {
        const appointmentId = draggableId;
        const targetSalle = destination.droppableId; // 'salle1' ou 'salle2'
        
        await updateAppointmentRoom(appointmentId, targetSalle);
        toast.success(`Patient déplacé vers ${targetSalle === 'salle1' ? 'Salle 1' : 'Salle 2'}`);
      } 
      // Réorganisation dans la même salle (priorité)
      else {
        const appointmentId = draggableId;
        const newPosition = destination.index + 1; // Position 1-based
        
        // TODO: Implémenter l'API pour la gestion des priorités
        // Pour l'instant, on simule juste un message
        toast.info(`Patient repositionné en position ${newPosition} dans ${source.droppableId === 'salle1' ? 'Salle 1' : 'Salle 2'}`);
      }
    } catch (error) {
      console.error('Error in drag and drop:', error);
      toast.error('Erreur lors du déplacement');
    }
  };

  // Calculer le temps d'attente estimé
  const calculateWaitingTime = (patients, currentPatientId) => {
    const currentIndex = patients.findIndex(p => p.id === currentPatientId);
    const patientsAhead = patients.slice(0, currentIndex).filter(p => p.statut === 'attente');
    const estimatedMinutes = patientsAhead.length * 15; // 15 min par patient
    
    return {
      minutes: estimatedMinutes,
      patientsAhead: patientsAhead.length,
      position: currentIndex + 1
    };
  };

  const PatientCard = ({ appointment, patients, onStart, onFinish, onMarkAbsent, onMoveToSalle, index, isDragging }) => {
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
      <div className={`p-4 rounded-lg border-2 ${getStatusColor(appointment.statut)} mb-3 transition-all duration-200 ${
        isDragging ? 'shadow-lg rotate-2 scale-105' : 'shadow-sm'
      }`}>
        {/* Header avec icône de drag */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3 flex-1">
            {/* Icône drag */}
            <GripVertical className="w-4 h-4 text-gray-400 cursor-grab" />
            
            <div className="flex-1">
              <h3 className="font-semibold text-lg">
                {appointment.patient?.prenom} {appointment.patient?.nom}
              </h3>
              <div className="flex items-center space-x-4 text-sm opacity-75 mt-1">
                <span>📅 {appointment.heure}</span>
                <span className={`px-2 py-1 rounded ${appointment.type_rdv === 'visite' ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'}`}>
                  {appointment.type_rdv === 'visite' ? '💰 Visite' : '🆓 Contrôle'}
                </span>
                <span className={`px-2 py-1 rounded ${appointment.paye ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                  {appointment.paye ? '✅ Payé' : '❌ Non payé'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Position dans la queue */}
            <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs font-medium">
              #{index + 1}
            </span>
            {getStatusIcon(appointment.statut)}
            <span className="text-sm font-medium capitalize">{appointment.statut}</span>
          </div>
        </div>

        {/* Temps d'attente */}
        {appointment.statut === 'attente' && (
          <div className="bg-white bg-opacity-50 p-2 rounded mb-3">
            <div className="flex items-center justify-between text-sm">
              <span>⏱️ Temps d'attente estimé: ~{waitingTime.minutes} min</span>
              <span>👥 Position: {waitingTime.position} ({waitingTime.patientsAhead} avant)</span>
            </div>
          </div>
        )}
        
        {/* Actions */}
        <div className="flex space-x-2">
          {appointment.statut === 'attente' && (
            <button
              onClick={() => onStart(appointment.id)}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded transition-colors"
            >
              🚀 Démarrer consultation
            </button>
          )}
          
          {appointment.statut === 'en_cours' && (
            <button
              onClick={() => onFinish(appointment.id)}
              className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded transition-colors"
            >
              ✅ Terminer consultation
            </button>
          )}
          
          {/* Bouton pour déplacer vers l'autre salle (manuel) */}
          {appointment.salle === 'salle1' && (
            <button
              onClick={() => onMoveToSalle(appointment.id, 'salle2')}
              className="bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded transition-colors"
            >
              → Salle 2
            </button>
          )}
          
          {appointment.salle === 'salle2' && (
            <button
              onClick={() => onMoveToSalle(appointment.id, 'salle1')}
              className="bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded transition-colors"
            >
              → Salle 1
            </button>
          )}
          
          <button
            onClick={() => onMarkAbsent(appointment.id)}
            className="p-2 text-red-500 hover:bg-red-100 rounded transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  const SalleColumn = ({ title, patients, color, onStart, onFinish, onMarkAbsent, onMoveToSalle }) => {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <span className={`bg-${color}-100 text-${color}-800 px-3 py-1 rounded-full text-sm font-medium`}>
            {patients.length} patient(s)
          </span>
        </div>
        
        <div className="space-y-3">
          {patients.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Aucun patient en attente</p>
            </div>
          ) : (
            patients.map((appointment) => (
              <PatientCard
                key={appointment.id}
                appointment={appointment}
                patients={patients}
                onStart={onStart}
                onFinish={onFinish}
                onMarkAbsent={onMarkAbsent}
                onMoveToSalle={onMoveToSalle}
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

  // Layout adaptatif : Si salle2 vide, salle1 prend toute la largeur
  const isSalle2Empty = salle2.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Salles d'attente</h1>
          <p className="text-gray-600">Gestion des patients en attente</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Dernière mise à jour</div>
          <div className="text-sm font-medium">{new Date().toLocaleTimeString()}</div>
        </div>
      </div>

      {/* Stats */}
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
            <DollarSign className="w-5 h-5 text-purple-500" />
            <span className="text-sm font-medium">Recettes</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">{stats.totalRecettes} TND</p>
        </div>
      </div>

      {/* Salles - Layout adaptatif */}
      <div className={`grid ${isSalle2Empty ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'} gap-6 transition-all duration-300`}>
        {/* Salle 1 - Toujours visible */}
        <SalleColumn
          title="Salle 1"
          patients={salle1}
          color="blue"
          onStart={startConsultation}
          onFinish={finishConsultation}
          onMarkAbsent={markAsAbsent}
          onMoveToSalle={updateAppointmentRoom}
        />

        {/* Salle 2 - Visible uniquement si elle a des patients */}
        {!isSalle2Empty && (
          <SalleColumn
            title="Salle 2"
            patients={salle2}
            color="green"
            onStart={startConsultation}
            onFinish={finishConsultation}
            onMarkAbsent={markAsAbsent}
            onMoveToSalle={updateAppointmentRoom}
          />
        )}
      </div>

      {/* Bouton flottant pour ajouter un RDV */}
      <button
        onClick={() => {
          // TODO: Ouvrir le modal d'ajout de RDV
          toast.info('Fonctionnalité d\'ajout de RDV - à implémenter dans Phase 7');
        }}
        className="fixed bottom-6 right-6 bg-primary-500 hover:bg-primary-600 text-white p-4 rounded-full shadow-lg transition-colors z-10"
      >
        <Plus className="w-6 h-6" />
      </button>
    </div>
  );
};

export default WaitingRoom;