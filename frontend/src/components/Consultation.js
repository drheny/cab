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
  Square,
  Minimize2,
  Maximize2,
  Phone,
  Calendar
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Consultation = ({ user }) => {
  const [consultationsEnCours, setConsultationsEnCours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [consultationModal, setConsultationModal] = useState({
    isOpen: false,
    isMinimized: false,
    appointmentId: null,
    patientInfo: null
  });
  
  // Chronomètre
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  
  // Données de la consultation
  const [consultationData, setConsultationData] = useState({
    poids: '',
    taille: '',
    pc: '',
    observation_medicale: '',
    traitement: '',
    bilans: '',
    relance_telephonique: false,
    date_relance: '',
    duree: 0
  });

  // Charger les consultations en cours
  useEffect(() => {
    fetchConsultationsEnCours();
  }, []);

  // Gestion du chronomètre
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

  const fetchConsultationsEnCours = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`/api/rdv/jour/${today}`);
      
      // Filtrer les patients en consultation (statut "en_cours")
      const consultations = response.data.filter(rdv => rdv.statut === "en_cours");
      setConsultationsEnCours(consultations);
    } catch (error) {
      console.error('Error fetching consultations:', error);
      toast.error('Erreur lors du chargement des consultations');
    } finally {
      setLoading(false);
    }
  };

  // Ouvrir le modal de consultation
  const ouvrirConsultation = (appointment) => {
    setConsultationModal({
      isOpen: true,
      isMinimized: false,
      appointmentId: appointment.id,
      patientInfo: appointment.patient
    });
    
    // Démarrer le chronomètre automatiquement
    setIsRunning(true);
    setTimer(0);
  };

  // Réduire le modal
  const reduireModal = () => {
    setConsultationModal(prev => ({
      ...prev,
      isMinimized: true
    }));
  };

  // Restaurer le modal
  const restaurerModal = () => {
    setConsultationModal(prev => ({
      ...prev,
      isMinimized: false
    }));
  };

  // Fermer le modal
  const fermerModal = () => {
    setConsultationModal({
      isOpen: false,
      isMinimized: false,
      appointmentId: null,
      patientInfo: null
    });
    setIsRunning(false);
    setTimer(0);
    resetConsultationData();
  };

  // Reset des données
  const resetConsultationData = () => {
    setConsultationData({
      poids: '',
      taille: '',
      pc: '',
      observation_medicale: '',
      traitement: '',
      bilans: '',
      relance_telephonique: false,
      date_relance: '',
      duree: 0
    });
  };

  // Sauvegarder la consultation
  const sauvegarderConsultation = async () => {
    try {
      // Arrêter le chronomètre
      setIsRunning(false);
      
      // Préparer les données
      const consultationPayload = {
        ...consultationData,
        duree: Math.floor(timer / 60), // Convertir en minutes
        patient_id: consultationsEnCours.find(c => c.id === consultationModal.appointmentId)?.patient_id,
        appointment_id: consultationModal.appointmentId,
        date: new Date().toISOString().split('T')[0]
      };

      // Sauvegarder la consultation
      await axios.post('/api/consultations', consultationPayload);
      
      // Changer le statut du RDV à "terminé"
      await axios.put(`/api/rdv/${consultationModal.appointmentId}/statut`, {
        statut: "termine"
      });

      toast.success('Consultation sauvegardée avec succès');
      fermerModal();
      fetchConsultationsEnCours();
    } catch (error) {
      console.error('Error saving consultation:', error);
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  // Formater le temps
  const formatTimer = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div>
          <h1 className="responsive-title font-bold text-gray-900">Consultations</h1>
          <p className="text-gray-600 responsive-text">Gestion des consultations en cours</p>
        </div>
      </div>

      {/* Liste des consultations en cours */}
      {consultationsEnCours.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune consultation en cours</h3>
          <p className="text-gray-500">Les patients en consultation apparaîtront ici</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {consultationsEnCours.map((consultation) => (
            <div key={consultation.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="bg-blue-100 p-3 rounded-full">
                    <User className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {consultation.patient?.prenom} {consultation.patient?.nom}
                    </h3>
                    <p className="text-sm text-gray-600">
                      RDV {consultation.heure} - {consultation.type_rdv}
                    </p>
                    <p className="text-sm text-gray-500">{consultation.motif}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                    En cours
                  </span>
                  <button
                    onClick={() => ouvrirConsultation(consultation)}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Consultation</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de consultation */}
      {consultationModal.isOpen && (
        <>
          {/* Modal réduit */}
          {consultationModal.isMinimized ? (
            <div className="fixed bottom-4 right-4 z-50">
              <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[300px]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-gray-900">
                      {consultationModal.patientInfo?.prenom} {consultationModal.patientInfo?.nom}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-mono text-blue-600">
                      {formatTimer(timer)}
                    </span>
                    <button
                      onClick={restaurerModal}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <Maximize2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Modal complet */
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  {/* Header du modal */}
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        Consultation - {consultationModal.patientInfo?.prenom} {consultationModal.patientInfo?.nom}
                      </h2>
                      <p className="text-gray-600">
                        {new Date().toLocaleDateString('fr-FR')} - {formatTimer(timer)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={reduireModal}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                      >
                        <Minimize2 className="w-5 h-5" />
                      </button>
                      <button
                        onClick={fermerModal}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                      >
                        ×
                      </button>
                    </div>
                  </div>

                  {/* Chronomètre */}
                  <div className="bg-blue-50 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Clock className="w-6 h-6 text-blue-600" />
                        <span className="text-lg font-semibold text-blue-900">
                          Durée: {formatTimer(timer)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setIsRunning(!isRunning)}
                          className={`p-2 rounded-lg ${
                            isRunning 
                              ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                              : 'bg-green-100 text-green-600 hover:bg-green-200'
                          }`}
                        >
                          {isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                        </button>
                        <button
                          onClick={() => {
                            setIsRunning(false);
                            setTimer(0);
                          }}
                          className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg"
                        >
                          <Square className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Formulaire de consultation */}
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    sauvegarderConsultation();
                  }}>
                    <div className="space-y-6">
                      {/* Mesures */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Mesures</h3>
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
                              onChange={(e) => setConsultationData({...consultationData, poids: e.target.value})}
                              className="input-field"
                              placeholder="0.0"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              <Ruler className="w-4 h-4 inline mr-1" />
                              Taille (cm)
                            </label>
                            <input
                              type="number"
                              value={consultationData.taille}
                              onChange={(e) => setConsultationData({...consultationData, taille: e.target.value})}
                              className="input-field"
                              placeholder="0"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              <Brain className="w-4 h-4 inline mr-1" />
                              PC (cm)
                            </label>
                            <input
                              type="number"
                              value={consultationData.pc}
                              onChange={(e) => setConsultationData({...consultationData, pc: e.target.value})}
                              className="input-field"
                              placeholder="0"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Observations et traitement */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Observation médicale
                          </label>
                          <textarea
                            value={consultationData.observation_medicale}
                            onChange={(e) => setConsultationData({...consultationData, observation_medicale: e.target.value})}
                            className="input-field"
                            rows="4"
                            placeholder="Observations du médecin..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Traitement
                          </label>
                          <textarea
                            value={consultationData.traitement}
                            onChange={(e) => setConsultationData({...consultationData, traitement: e.target.value})}
                            className="input-field"
                            rows="4"
                            placeholder="Traitement prescrit..."
                          />
                        </div>
                      </div>

                      {/* Bilans */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Bilans
                        </label>
                        <textarea
                          value={consultationData.bilans}
                          onChange={(e) => setConsultationData({...consultationData, bilans: e.target.value})}
                          className="input-field"
                          rows="3"
                          placeholder="Bilans demandés..."
                        />
                      </div>

                      {/* Relance téléphonique */}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Relance téléphonique</h3>
                        <div className="flex items-center space-x-4">
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={consultationData.relance_telephonique}
                              onChange={(e) => setConsultationData({...consultationData, relance_telephonique: e.target.checked})}
                              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                              <Phone className="w-4 h-4 inline mr-1" />
                              Programmer une relance
                            </span>
                          </label>
                          {consultationData.relance_telephonique && (
                            <div>
                              <input
                                type="date"
                                value={consultationData.date_relance}
                                onChange={(e) => setConsultationData({...consultationData, date_relance: e.target.value})}
                                className="input-field"
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Boutons */}
                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        type="button"
                        onClick={fermerModal}
                        className="btn-outline"
                      >
                        Annuler
                      </button>
                      <button
                        type="submit"
                        className="btn-primary flex items-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>Sauvegarder</span>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Consultation;