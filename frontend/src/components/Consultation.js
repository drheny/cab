import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  User, 
  Weight, 
  Ruler, 
  Brain,
  FileText,
  Save,
  Play,
  Pause,
  Stop
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Consultation = ({ user }) => {
  const [activeConsultations, setActiveConsultations] = useState([]);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [consultationData, setConsultationData] = useState({
    poids: '',
    taille: '',
    pc: '',
    observations: '',
    traitement: '',
    bilan: '',
    relance_date: ''
  });

  useEffect(() => {
    fetchActiveConsultations();
  }, []);

  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setTimer(timer => timer + 1);
      }, 1000);
    } else if (!isRunning && timer !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRunning, timer]);

  const fetchActiveConsultations = async () => {
    try {
      const response = await axios.get('/api/appointments/today');
      const inProgressAppointments = response.data.filter(apt => apt.statut === 'en_cours');
      setActiveConsultations(inProgressAppointments);
      
      if (inProgressAppointments.length > 0 && !selectedConsultation) {
        setSelectedConsultation(inProgressAppointments[0]);
      }
    } catch (error) {
      console.error('Error fetching consultations:', error);
      toast.error('Erreur lors du chargement des consultations');
    } finally {
      setLoading(false);
    }
  };

  const startTimer = () => {
    setIsRunning(true);
  };

  const pauseTimer = () => {
    setIsRunning(false);
  };

  const stopTimer = () => {
    setIsRunning(false);
    setTimer(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSaveConsultation = async () => {
    if (!selectedConsultation) return;

    try {
      const consultationPayload = {
        patient_id: selectedConsultation.patient_id,
        appointment_id: selectedConsultation.id,
        date: new Date().toISOString().split('T')[0],
        duree: Math.floor(timer / 60),
        poids: parseFloat(consultationData.poids) || 0,
        taille: parseFloat(consultationData.taille) || 0,
        pc: parseFloat(consultationData.pc) || 0,
        observations: consultationData.observations,
        traitement: consultationData.traitement,
        bilan: consultationData.bilan,
        relance_date: consultationData.relance_date
      };

      await axios.post('/api/consultations', consultationPayload);
      
      // Mettre à jour le statut du rendez-vous
      const updatedAppointment = {
        ...selectedConsultation,
        statut: 'termine'
      };
      
      await axios.put(`/api/appointments/${selectedConsultation.id}`, updatedAppointment);
      
      toast.success('Consultation enregistrée avec succès');
      
      // Reset form
      setConsultationData({
        poids: '',
        taille: '',
        pc: '',
        observations: '',
        traitement: '',
        bilan: '',
        relance_date: ''
      });
      
      stopTimer();
      fetchActiveConsultations();
    } catch (error) {
      console.error('Error saving consultation:', error);
      toast.error('Erreur lors de l\'enregistrement');
    }
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
        <h1 className="text-2xl font-bold text-gray-900">Consultation</h1>
        <p className="text-gray-600">Suivi des consultations en cours</p>
      </div>

      {activeConsultations.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune consultation en cours
          </h3>
          <p className="text-gray-500">
            Démarrez une consultation depuis les salles d'attente
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar - Active Consultations */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Consultations actives
              </h2>
              <div className="space-y-3">
                {activeConsultations.map((consultation) => (
                  <div
                    key={consultation.id}
                    onClick={() => setSelectedConsultation(consultation)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedConsultation?.id === consultation.id
                        ? 'bg-primary-100 border-primary-200'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="bg-primary-500 p-2 rounded-full">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">
                          {consultation.patient?.prenom} {consultation.patient?.nom}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {consultation.heure} - {consultation.salle}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            {selectedConsultation && (
              <div className="space-y-6">
                {/* Patient Info & Timer */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className="bg-primary-100 p-3 rounded-full">
                        <User className="w-6 h-6 text-primary-600" />
                      </div>
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          {selectedConsultation.patient?.prenom} {selectedConsultation.patient?.nom}
                        </h2>
                        <p className="text-gray-600">
                          {selectedConsultation.heure} - {selectedConsultation.salle}
                        </p>
                      </div>
                    </div>
                    
                    {/* Timer */}
                    <div className="text-center">
                      <div className="text-3xl font-bold text-primary-600 mb-2">
                        {formatTime(timer)}
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={startTimer}
                          className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                        <button
                          onClick={pauseTimer}
                          className="p-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                        <button
                          onClick={stopTimer}
                          className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg"
                        >
                          <Stop className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Consultation Form */}
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">
                    Fiche de consultation
                  </h3>

                  <div className="space-y-6">
                    {/* Mesures */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Mesures</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Weight className="w-4 h-4 inline mr-1" />
                            Poids (kg)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            value={consultationData.poids}
                            onChange={(e) => setConsultationData({
                              ...consultationData,
                              poids: e.target.value
                            })}
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
                            value={consultationData.taille}
                            onChange={(e) => setConsultationData({
                              ...consultationData,
                              taille: e.target.value
                            })}
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
                            value={consultationData.pc}
                            onChange={(e) => setConsultationData({
                              ...consultationData,
                              pc: e.target.value
                            })}
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
                        value={consultationData.observations}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          observations: e.target.value
                        })}
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
                        value={consultationData.traitement}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          traitement: e.target.value
                        })}
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
                        value={consultationData.bilan}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          bilan: e.target.value
                        })}
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
                        value={consultationData.relance_date}
                        onChange={(e) => setConsultationData({
                          ...consultationData,
                          relance_date: e.target.value
                        })}
                        className="input-field"
                      />
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={handleSaveConsultation}
                        className="btn-primary flex items-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>Enregistrer la consultation</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Consultation;