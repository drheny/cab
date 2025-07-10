import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Users, 
  DollarSign, 
  CheckCircle, 
  ArrowRight,
  Plus,
  Trash2
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const WaitingRoom = ({ user }) => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [salle1, setSalle1] = useState([]);
  const [salle2, setSalle2] = useState([]);

  useEffect(() => {
    fetchTodayAppointments();
  }, []);

  const fetchTodayAppointments = async () => {
    try {
      const response = await axios.get('/api/appointments/today');
      setAppointments(response.data);
      
      // Séparer les patients par salle
      const salle1Patients = response.data.filter(apt => apt.salle === 'salle1');
      const salle2Patients = response.data.filter(apt => apt.salle === 'salle2');
      
      setSalle1(salle1Patients);
      setSalle2(salle2Patients);
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

      const updatedAppointment = {
        ...appointment,
        statut: newStatus,
        salle: salle || appointment.salle
      };

      await axios.put(`/api/appointments/${appointmentId}`, updatedAppointment);
      toast.success('Statut mis à jour avec succès');
      fetchTodayAppointments();
    } catch (error) {
      console.error('Error updating appointment:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const moveToSalle = (appointmentId, targetSalle) => {
    updateAppointmentStatus(appointmentId, 'attente', targetSalle);
  };

  const startConsultation = (appointmentId) => {
    updateAppointmentStatus(appointmentId, 'en_cours');
  };

  const finishConsultation = (appointmentId) => {
    updateAppointmentStatus(appointmentId, 'termine');
  };

  const createPayment = async (appointmentId, amount) => {
    try {
      const appointment = appointments.find(apt => apt.id === appointmentId);
      if (!appointment) return;

      const paymentData = {
        patient_id: appointment.patient_id,
        appointment_id: appointmentId,
        montant: amount,
        type_paiement: 'espece',
        statut: 'paye',
        date: new Date().toISOString().split('T')[0]
      };

      await axios.post('/api/payments', paymentData);
      toast.success('Paiement enregistré avec succès');
    } catch (error) {
      console.error('Error creating payment:', error);
      toast.error('Erreur lors de l\'enregistrement du paiement');
    }
  };

  const PatientCard = ({ appointment, onMove, onStart, onFinish, onPay, onRemove }) => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'attente': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        case 'en_cours': return 'bg-blue-100 text-blue-800 border-blue-200';
        case 'termine': return 'bg-green-100 text-green-800 border-green-200';
        default: return 'bg-gray-100 text-gray-800 border-gray-200';
      }
    };

    return (
      <div className={`p-4 rounded-lg border-2 ${getStatusColor(appointment.statut)} mb-3`}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="font-semibold">
              {appointment.patient?.prenom} {appointment.patient?.nom}
            </h3>
            <p className="text-sm opacity-75">{appointment.heure}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">15 min</span>
          </div>
        </div>
        
        <div className="flex space-x-2">
          {appointment.statut === 'attente' && (
            <button
              onClick={() => onStart(appointment.id)}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-1 px-2 rounded"
            >
              Consultation
            </button>
          )}
          
          {appointment.statut === 'en_cours' && (
            <button
              onClick={() => onFinish(appointment.id)}
              className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-1 px-2 rounded"
            >
              Terminer
            </button>
          )}
          
          {appointment.type_rdv === 'visite' && (
            <button
              onClick={() => onPay(appointment.id, 300)}
              className="flex-1 bg-purple-500 hover:bg-purple-600 text-white text-sm py-1 px-2 rounded"
            >
              Payer 300 DH
            </button>
          )}
          
          <button
            onClick={() => onRemove(appointment.id)}
            className="p-1 text-red-500 hover:bg-red-100 rounded"
          >
            <Trash2 className="w-4 h-4" />
          </button>
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Salles d'attente</h1>
        <p className="text-gray-600">Gestion des patients en attente</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-500" />
            <span className="text-sm font-medium">Salle 1</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{salle1.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium">Salle 2</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{salle2.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-yellow-500" />
            <span className="text-sm font-medium">En cours</span>
          </div>
          <p className="text-2xl font-bold text-yellow-600">
            {appointments.filter(apt => apt.statut === 'en_cours').length}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-purple-500" />
            <span className="text-sm font-medium">Terminés</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">
            {appointments.filter(apt => apt.statut === 'termine').length}
          </p>
        </div>
      </div>

      {/* Salles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Salle 1 */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Salle 1</h2>
            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
              {salle1.length} patient(s)
            </span>
          </div>
          
          <div className="space-y-3">
            {salle1.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Aucun patient en attente</p>
              </div>
            ) : (
              salle1.map((appointment) => (
                <PatientCard
                  key={appointment.id}
                  appointment={appointment}
                  onMove={(id) => moveToSalle(id, 'salle2')}
                  onStart={startConsultation}
                  onFinish={finishConsultation}
                  onPay={createPayment}
                  onRemove={(id) => updateAppointmentStatus(id, 'absent')}
                />
              ))
            )}
          </div>
        </div>

        {/* Salle 2 */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Salle 2</h2>
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              {salle2.length} patient(s)
            </span>
          </div>
          
          <div className="space-y-3">
            {salle2.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Aucun patient en attente</p>
              </div>
            ) : (
              salle2.map((appointment) => (
                <PatientCard
                  key={appointment.id}
                  appointment={appointment}
                  onMove={(id) => moveToSalle(id, 'salle1')}
                  onStart={startConsultation}
                  onFinish={finishConsultation}
                  onPay={createPayment}
                  onRemove={(id) => updateAppointmentStatus(id, 'absent')}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Patients restants */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Patients restants</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {appointments
            .filter(apt => apt.statut === 'absent')
            .map((appointment) => (
              <div key={appointment.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-medium">
                      {appointment.patient?.prenom} {appointment.patient?.nom}
                    </h3>
                    <p className="text-sm text-gray-500">{appointment.heure}</p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => moveToSalle(appointment.id, 'salle1')}
                    className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-1 px-2 rounded"
                  >
                    Salle 1
                  </button>
                  <button
                    onClick={() => moveToSalle(appointment.id, 'salle2')}
                    className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-1 px-2 rounded"
                  >
                    Salle 2
                  </button>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default WaitingRoom;