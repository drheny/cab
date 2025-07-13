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
  GripVertical,
  MessageCircle,
  Eye,
  Send,
  Euro,
  Banknote,
  Smartphone
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

  // **PHASE 4: WhatsApp Integration**
  const [whatsappStates, setWhatsappStates] = useState({}); // Tracking WhatsApp sent status

  // **PHASE 5: Payment Integration**
  const [paymentStates, setPaymentStates] = useState({}); // Tracking payment status

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
      
      // Gérer différents formats de réponse API
      const appointmentsData = response.data.rdv || response.data || [];
      
      console.log('Fetched appointments:', appointmentsData); // Debug log
      
      setAppointments(appointmentsData);
      
      // Séparer les patients par salle (seulement ceux en attente ou en consultation)
      const salle1Patients = appointmentsData.filter(apt => {
        console.log(`Patient ${apt.patient?.prenom}: statut=${apt.statut}, salle=${apt.salle}`); // Debug log
        return apt.salle === 'salle1' && ['attente', 'en_cours'].includes(apt.statut);
      });
      const salle2Patients = appointmentsData.filter(apt => 
        apt.salle === 'salle2' && ['attente', 'en_cours'].includes(apt.statut)
      );
      
      console.log('Salle1 patients:', salle1Patients); // Debug log
      console.log('Salle2 patients:', salle2Patients); // Debug log
      
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

  // **PHASE 3: Calcul temps d'attente en temps réel amélioré**
  const calculateWaitingTime = (patients, currentPatientId) => {
    const currentIndex = patients.findIndex(p => p.id === currentPatientId);
    if (currentIndex === -1) return { minutes: 0, patientsAhead: 0, position: 0, estimatedTime: null };
    
    // Filtrer seulement les patients en attente avant le patient actuel
    const patientsAhead = patients.slice(0, currentIndex).filter(p => p.statut === 'attente');
    
    // Calculer le temps estimé (15 min par patient en attente + temps pour patient en cours)
    let estimatedMinutes = patientsAhead.length * 15;
    
    // Ajouter du temps si un patient est actuellement en consultation
    const patientInConsultation = patients.find(p => p.statut === 'en_cours');
    if (patientInConsultation) {
      // Estimer qu'il reste 10 minutes en moyenne pour le patient en cours
      estimatedMinutes += 10;
    }
    
    // Calculer l'heure estimée
    const now = new Date();
    const estimatedTime = new Date(now.getTime() + estimatedMinutes * 60000);
    
    return {
      minutes: estimatedMinutes,
      patientsAhead: patientsAhead.length,
      position: currentIndex + 1,
      estimatedTime: estimatedTime,
      timeString: estimatedTime.toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    };
  };

  // Calcul global du temps d'attente moyen pour les statistiques
  const calculateAverageWaitingTime = () => {
    const allWaitingPatients = [...salle1, ...salle2].filter(p => p.statut === 'attente');
    if (allWaitingPatients.length === 0) return 0;
    
    const totalWaitingTime = allWaitingPatients.reduce((total, patient, index) => {
      const waitingTime = calculateWaitingTime(allWaitingPatients, patient.id);
      return total + waitingTime.minutes;
    }, 0);
    
    return Math.round(totalWaitingTime / allWaitingPatients.length);
  };

  // État pour le temps d'attente moyen
  const [averageWaitingTime, setAverageWaitingTime] = useState(0);

  // Mise à jour temps réel toutes les minutes
  useEffect(() => {
    const updateWaitingTimes = () => {
      const avgTime = calculateAverageWaitingTime();
      setAverageWaitingTime(avgTime);
    };

    // Calculer immédiatement
    updateWaitingTimes();

    // Mettre à jour toutes les minutes
    const interval = setInterval(updateWaitingTimes, 60000);
    return () => clearInterval(interval);
  }, [salle1, salle2]);

  // **PHASE 4: WhatsApp Integration**
  
  // Template de message WhatsApp
  const generateWhatsAppMessage = (patient, waitingTime, salle) => {
    const salleText = salle === 'salle1' ? 'Salle 1' : 'Salle 2';
    const message = `🏥 *Cabinet Dr. [Nom Docteur]*

Bonjour ${patient.prenom},

📍 *Votre statut*
• Salle d'attente: ${salleText}
• Position dans la file: #${waitingTime.position}

⏱️ *Temps d'attente estimé*
• Environ ${waitingTime.minutes} minutes
• Heure prévue: vers ${waitingTime.timeString}

👥 *File d'attente*
${waitingTime.patientsAhead === 0 
  ? '🎯 Vous êtes le prochain patient !'
  : `• ${waitingTime.patientsAhead} patient(s) avant vous`
}

💡 *Informations utiles*
• Merci de rester disponible
• Votre tour approche
• En cas d'urgence: appelez le cabinet

Merci de votre patience ! 🙏`;

    return message;
  };

  // Envoi du message WhatsApp
  const sendWhatsAppMessage = async (appointment, salle) => {
    try {
      // Calculer les temps d'attente actuels
      const patients = salle === 'salle1' ? salle1 : salle2;
      const waitingTime = calculateWaitingTime(patients, appointment.id);
      
      // Générer le message
      const message = generateWhatsAppMessage(appointment.patient, waitingTime, salle);
      
      // Encoder le message pour URL
      const encodedMessage = encodeURIComponent(message);
      
      // Générer le lien WhatsApp
      const phoneNumber = appointment.patient.numero_whatsapp || appointment.patient.telephone;
      const formattedPhone = phoneNumber.startsWith('216') ? phoneNumber : `216${phoneNumber}`;
      const whatsappUrl = `https://wa.me/${formattedPhone}?text=${encodedMessage}`;
      
      // Ouvrir WhatsApp dans un nouvel onglet
      window.open(whatsappUrl, '_blank');
      
      // Marquer comme envoyé avec horodatage
      const timestamp = new Date().toLocaleString('fr-FR');
      setWhatsappStates(prev => ({
        ...prev,
        [appointment.id]: {
          sent: true,
          timestamp: timestamp,
          message: message
        }
      }));
      
      // Optionnel: Enregistrer l'envoi dans la base de données
      try {
        await axios.put(`${API_BASE_URL}/api/rdv/${appointment.id}/whatsapp`, {
          whatsapp_envoye: true,
          whatsapp_timestamp: timestamp
        });
      } catch (dbError) {
        console.log('Could not save WhatsApp status to database:', dbError);
        // Continuer quand même, l'envoi WhatsApp a réussi
      }
      
      toast.success(`Message WhatsApp envoyé à ${appointment.patient.prenom}`);
      
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
      toast.error('Erreur lors de l\'envoi du message WhatsApp');
    }
  };

  // Fonction pour prévisualiser le message
  const [showWhatsAppPreview, setShowWhatsAppPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  const previewWhatsAppMessage = (appointment, salle) => {
    const patients = salle === 'salle1' ? salle1 : salle2;
    const waitingTime = calculateWaitingTime(patients, appointment.id);
    const message = generateWhatsAppMessage(appointment.patient, waitingTime, salle);
    
    setPreviewData({
      appointment,
      salle,
      waitingTime,
      message
    });
    setShowWhatsAppPreview(true);
  };

  const confirmSendWhatsApp = () => {
    if (previewData) {
      sendWhatsAppMessage(previewData.appointment, previewData.salle);
      setShowWhatsAppPreview(false);
      setPreviewData(null);
    }
  };

  // **PHASE 5: Payment Integration**
  
  // Calculer le montant du paiement selon le type
  const calculatePaymentAmount = (appointment) => {
    if (appointment.type_rdv === 'controle') return 0; // Contrôle gratuit
    
    // Pour les visites payantes
    const baseAmount = 300; // TND
    
    // TODO: Ajouter logique assurance si nécessaire
    // if (appointment.assurance) return 50; // Ticket modérateur
    
    return baseAmount;
  };

  // Mettre à jour le statut de paiement
  const updatePaymentStatus = async (appointmentId, isPaid, amount = 0, paymentMethod = 'espece') => {
    try {
      const updateData = {
        paye: isPaid,
        montant_paye: amount,
        methode_paiement: paymentMethod,
        date_paiement: isPaid ? new Date().toISOString() : null
      };

      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/paiement`, updateData);
      
      // Mettre à jour l'état local
      setPaymentStates(prev => ({
        ...prev,
        [appointmentId]: {
          paid: isPaid,
          amount: amount,
          method: paymentMethod,
          timestamp: isPaid ? new Date().toLocaleString('fr-FR') : null
        }
      }));

      toast.success(isPaid ? `Paiement de ${amount} TND enregistré` : 'Paiement annulé');
      
      // Rafraîchir les données
      fetchTodayAppointments();
      
    } catch (error) {
      console.error('Error updating payment:', error);
      toast.error('Erreur lors de la mise à jour du paiement');
    }
  };

  // Marquer comme payé
  const markAsPaid = (appointment, paymentMethod = 'espece') => {
    const amount = calculatePaymentAmount(appointment);
    updatePaymentStatus(appointment.id, true, amount, paymentMethod);
  };

  // Marquer comme non payé
  const markAsUnpaid = (appointment) => {
    updatePaymentStatus(appointment.id, false, 0);
  };

  // Ouvrir le modal de paiement détaillé
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPaymentAppointment, setSelectedPaymentAppointment] = useState(null);

  const openPaymentModal = (appointment) => {
    setSelectedPaymentAppointment(appointment);
    setShowPaymentModal(true);
  };

  // **PHASE 7: Bouton ajout RDV urgents**
  const [showUrgentModal, setShowUrgentModal] = useState(false);
  const [urgentFormData, setUrgentFormData] = useState({
    patient_nom: '',
    patient_prenom: '',
    patient_telephone: '',
    type_rdv: 'visite',
    salle: 'salle1',
    notes: ''
  });

  const handleUrgentRDV = () => {
    setShowUrgentModal(true);
    // Pré-remplir avec heure actuelle
    const now = new Date();
    const currentTime = now.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    
    setUrgentFormData(prev => ({
      ...prev,
      heure: currentTime
    }));
  };

  const createUrgentAppointment = async () => {
    try {
      if (!urgentFormData.patient_nom || !urgentFormData.patient_prenom || !urgentFormData.patient_telephone) {
        toast.error('Veuillez remplir tous les champs obligatoires');
        return;
      }

      // Créer le patient d'urgence
      const patientId = 'urgent_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      
      const patientData = {
        id: patientId,
        nom: urgentFormData.patient_nom,
        prenom: urgentFormData.patient_prenom,
        telephone: urgentFormData.patient_telephone,
        date_naissance: '',
        adresse: '',
        pere: { nom: '', telephone: '', fonction: '' },
        mere: { nom: '', telephone: '', fonction: '' },
        numero_whatsapp: urgentFormData.patient_telephone,
        notes: 'Patient urgent - créé depuis salle d\'attente',
        antecedents: '',
        consultations: []
      };

      // Créer le patient
      await axios.post(`${API_BASE_URL}/api/patients`, patientData);

      // Créer le RDV urgent
      const appointmentData = {
        id: 'rdv_urgent_' + Date.now(),
        patient_id: patientId,
        date: new Date().toISOString().split('T')[0],
        heure: urgentFormData.heure || new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        statut: 'attente', // Directement en attente
        type_rdv: urgentFormData.type_rdv,
        salle: urgentFormData.salle,
        paye: false,
        notes_rdv: `URGENT - ${urgentFormData.notes}`,
        rappel_envoye: false
      };

      await axios.post(`${API_BASE_URL}/api/rdv`, appointmentData);

      toast.success(`RDV urgent créé pour ${urgentFormData.patient_prenom} ${urgentFormData.patient_nom}`);
      
      // Reset form et fermer modal
      setUrgentFormData({
        patient_nom: '',
        patient_prenom: '',
        patient_telephone: '',
        type_rdv: 'visite',
        salle: 'salle1',
        notes: ''
      });
      setShowUrgentModal(false);
      
      // Rafraîchir les données
      fetchTodayAppointments();
      
    } catch (error) {
      console.error('Error creating urgent appointment:', error);
      toast.error('Erreur lors de la création du RDV urgent');
    }
  };

  const PatientCard = ({ 
    appointment, 
    patients, 
    onStart, 
    onFinish, 
    onMarkAbsent, 
    onMoveToSalle, 
    index, 
    isDragging,
    whatsappStates,
    onSendWhatsApp,
    onPreviewWhatsApp,
    paymentStates,
    onMarkPaid,
    onMarkUnpaid,
    onOpenPaymentModal
  }) => {
    const waitingTime = calculateWaitingTime(patients, appointment.id);
    const paymentAmount = calculatePaymentAmount(appointment);
    
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

    const getPaymentStatusInfo = () => {
      if (appointment.type_rdv === 'controle') {
        return { 
          status: 'gratuit', 
          color: 'bg-green-100 text-green-800', 
          text: '🆓 Gratuit',
          amount: 0
        };
      }
      
      const isPaid = appointment.paye || paymentStates[appointment.id]?.paid;
      if (isPaid) {
        return { 
          status: 'paye', 
          color: 'bg-green-100 text-green-800', 
          text: `✅ Payé ${paymentAmount} TND`,
          amount: paymentAmount
        };
      } else {
        return { 
          status: 'non_paye', 
          color: 'bg-red-100 text-red-800', 
          text: `❌ Non payé ${paymentAmount} TND`,
          amount: paymentAmount
        };
      }
    };

    const paymentInfo = getPaymentStatusInfo();

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
                <span className={`px-2 py-1 rounded ${paymentInfo.color}`}>
                  {paymentInfo.text}
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

        {/* Module Paiement */}
        {appointment.type_rdv === 'visite' && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-purple-800">💳 Gestion Paiement</span>
              <span className="text-lg font-bold text-purple-900">{paymentAmount} TND</span>
            </div>
            
            <div className="flex space-x-2">
              {!appointment.paye && !paymentStates[appointment.id]?.paid ? (
                <>
                  <button
                    onClick={() => onMarkPaid(appointment, 'espece')}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs py-1 px-2 rounded transition-colors flex items-center justify-center space-x-1"
                    title="Marquer comme payé en espèces"
                  >
                    <Banknote className="w-3 h-3" />
                    <span>Espèces</span>
                  </button>
                  <button
                    onClick={() => onMarkPaid(appointment, 'carte')}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs py-1 px-2 rounded transition-colors flex items-center justify-center space-x-1"
                    title="Marquer comme payé par carte"
                  >
                    <CreditCard className="w-3 h-3" />
                    <span>Carte</span>
                  </button>
                  <button
                    onClick={() => onOpenPaymentModal(appointment)}
                    className="bg-gray-500 hover:bg-gray-600 text-white text-xs py-1 px-2 rounded transition-colors"
                    title="Options avancées"
                  >
                    <Euro className="w-3 h-3" />
                  </button>
                </>
              ) : (
                <>
                  <div className="flex-1 bg-green-100 text-green-800 text-xs py-1 px-2 rounded flex items-center justify-center space-x-1">
                    <CheckCircle className="w-3 h-3" />
                    <span>Payé - {paymentStates[appointment.id]?.method || 'espece'}</span>
                  </div>
                  <button
                    onClick={() => onMarkUnpaid(appointment)}
                    className="bg-red-500 hover:bg-red-600 text-white text-xs py-1 px-2 rounded transition-colors"
                    title="Annuler le paiement"
                  >
                    ❌
                  </button>
                </>
              )}
            </div>
            
            {(appointment.paye || paymentStates[appointment.id]?.paid) && paymentStates[appointment.id]?.timestamp && (
              <div className="mt-2 text-xs text-green-600">
                Payé le {paymentStates[appointment.id].timestamp}
              </div>
            )}
          </div>
        )}

        {/* Temps d'attente amélioré avec WhatsApp */}
        {appointment.statut === 'attente' && (
          <div className="bg-white bg-opacity-50 p-3 rounded mb-3 border-l-4 border-blue-400">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">⏱️ Temps estimé:</span>
                <div className="text-lg font-bold text-blue-600">~{waitingTime.minutes} min</div>
                <div className="text-xs text-gray-500">Vers {waitingTime.timeString}</div>
              </div>
              <div>
                <span className="font-medium text-gray-700">👥 File d'attente:</span>
                <div className="text-lg font-bold text-gray-600">Position #{waitingTime.position}</div>
                <div className="text-xs text-gray-500">
                  {waitingTime.patientsAhead === 0 
                    ? 'Prochain patient !' 
                    : `${waitingTime.patientsAhead} patient(s) avant`
                  }
                </div>
              </div>
            </div>
            
            {/* Barre de progression visuelle */}
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Attente</span>
                <span>Consultation</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${Math.max(10, 100 - (waitingTime.minutes / 60) * 100)}%` 
                  }}
                ></div>
              </div>
            </div>
            
            {/* Section WhatsApp */}
            <div className="mt-3 pt-2 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">📱 Communication patient</span>
                {whatsappStates[appointment.id]?.sent && (
                  <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                    ✅ Envoyé {whatsappStates[appointment.id].timestamp}
                  </span>
                )}
              </div>
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={() => onPreviewWhatsApp(appointment, appointment.salle)}
                  className="flex-1 bg-gray-500 hover:bg-gray-600 text-white text-xs py-1 px-2 rounded transition-colors flex items-center justify-center space-x-1"
                  title="Prévisualiser le message"
                >
                  <Eye className="w-3 h-3" />
                  <span>Aperçu</span>
                </button>
                <button
                  onClick={() => onSendWhatsApp(appointment, appointment.salle)}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs py-1 px-2 rounded transition-colors flex items-center justify-center space-x-1"
                  title="Envoyer message WhatsApp avec temps d'attente"
                >
                  <MessageCircle className="w-3 h-3" />
                  <span>WhatsApp</span>
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Actions principales avec logique contextuelle avancée */}
        <div className="flex space-x-2">
          {/* Actions selon le statut - PHASE 6: Workflow intelligent */}
          {appointment.statut === 'attente' && (
            <>
              <button
                onClick={() => onStart(appointment.id)}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded transition-colors flex items-center justify-center space-x-1"
                title="Commencer la consultation"
              >
                <Users className="w-4 h-4" />
                <span>🚀 Démarrer consultation</span>
              </button>
              
              {/* Actions secondaires pour patients en attente */}
              <button
                onClick={() => onMoveToSalle(appointment.id, appointment.salle === 'salle1' ? 'salle2' : 'salle1')}
                className="bg-purple-500 hover:bg-purple-600 text-white text-sm py-2 px-3 rounded transition-colors"
                title={`Déplacer vers ${appointment.salle === 'salle1' ? 'Salle 2' : 'Salle 1'}`}
              >
                {appointment.salle === 'salle1' ? '→ S2' : '→ S1'}
              </button>
            </>
          )}
          
          {appointment.statut === 'en_cours' && (
            <>
              <button
                onClick={() => onFinish(appointment.id)}
                className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded transition-colors flex items-center justify-center space-x-1"
                title="Terminer la consultation"
              >
                <CheckCircle className="w-4 h-4" />
                <span>✅ Terminer consultation</span>
              </button>
              
              {/* Indicateur consultation en cours */}
              <div className="bg-blue-100 text-blue-800 text-sm py-2 px-3 rounded flex items-center space-x-1">
                <Clock className="w-4 h-4 animate-pulse" />
                <span>En consultation</span>
              </div>
            </>
          )}
          
          {appointment.statut === 'termine' && (
            <>
              {/* Patient terminé - Actions post-consultation */}
              <div className="flex-1 bg-gray-100 text-gray-600 text-sm py-2 px-3 rounded flex items-center justify-center space-x-1">
                <CheckCircle className="w-4 h-4" />
                <span>Consultation terminée</span>
              </div>
              
              {appointment.type_rdv === 'visite' && !appointment.paye && !paymentStates[appointment.id]?.paid && (
                <button
                  onClick={() => onMarkPaid(appointment, 'espece')}
                  className="bg-green-600 hover:bg-green-700 text-white text-sm py-2 px-3 rounded transition-colors flex items-center space-x-1"
                  title="Finaliser le paiement"
                >
                  <DollarSign className="w-4 h-4" />
                  <span>Paiement</span>
                </button>
              )}
            </>
          )}
          
          {/* Action commune: Marquer absent */}
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
    onMarkAbsent, 
    onMoveToSalle, 
    salleId,
    whatsappStates,
    onSendWhatsApp,
    onPreviewWhatsApp,
    paymentStates,
    onMarkPaid,
    onMarkUnpaid,
    onOpenPaymentModal
  }) => {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <span className={`bg-${color}-100 text-${color}-800 px-3 py-1 rounded-full text-sm font-medium`}>
            {patients.length} patient(s)
          </span>
        </div>
        
        <Droppable droppableId={salleId}>
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className={`space-y-3 min-h-32 transition-colors duration-200 ${
                snapshot.isDraggingOver 
                  ? 'bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg p-2' 
                  : ''
              }`}
            >
              {patients.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Aucun patient en attente</p>
                  {snapshot.isDraggingOver && (
                    <p className="text-blue-600 font-medium mt-2">Déposer le patient ici</p>
                  )}
                </div>
              ) : (
                patients.map((appointment, index) => (
                  <Draggable 
                    key={appointment.id} 
                    draggableId={appointment.id} 
                    index={index}
                    isDragDisabled={appointment.statut === 'en_cours'} // Pas de drag si en consultation
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                      >
                        <PatientCard
                          appointment={appointment}
                          patients={patients}
                          onStart={onStart}
                          onFinish={onFinish}
                          onMarkAbsent={onMarkAbsent}
                          onMoveToSalle={onMoveToSalle}
                          index={index}
                          isDragging={snapshot.isDragging}
                          whatsappStates={whatsappStates}
                          onSendWhatsApp={onSendWhatsApp}
                          onPreviewWhatsApp={onPreviewWhatsApp}
                          paymentStates={paymentStates}
                          onMarkPaid={onMarkPaid}
                          onMarkUnpaid={onMarkUnpaid}
                          onOpenPaymentModal={onOpenPaymentModal}
                        />
                      </div>
                    )}
                  </Draggable>
                ))
              )}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
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
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Salles d'attente</h1>
            <p className="text-gray-600">Gestion des patients en attente • Glisser-déposer pour réorganiser</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Dernière mise à jour</div>
            <div className="text-sm font-medium">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Stats avec temps d'attente moyen */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
              <Clock className="w-5 h-5 text-orange-500" />
              <span className="text-sm font-medium">Attente moyenne</span>
            </div>
            <p className="text-2xl font-bold text-orange-600">{averageWaitingTime} min</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-medium">Recettes</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">{stats.totalRecettes} TND</p>
          </div>
        </div>

        {/* Instructions Drag & Drop avec temps réel */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-blue-800">
              <GripVertical className="w-5 h-5" />
              <span className="font-medium">Drag & Drop activé</span>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-600">Temps réel</span>
              </div>
              <span className="text-gray-500">Mise à jour: {new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>
          <p className="text-blue-700 text-sm mt-1">
            Glissez les patients entre les salles ou réorganisez l'ordre de priorité. 
            Les temps d'attente se mettent à jour automatiquement toutes les minutes.
          </p>
        </div>

        {/* Salles - Layout adaptatif avec Drag & Drop */}
        <div className={`grid ${isSalle2Empty ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'} gap-6 transition-all duration-300`}>
          {/* Salle 1 - Toujours visible */}
          <SalleColumn
            title="Salle 1"
            patients={salle1}
            color="blue"
            salleId="salle1"
            onStart={startConsultation}
            onFinish={finishConsultation}
            onMarkAbsent={markAsAbsent}
            onMoveToSalle={updateAppointmentRoom}
            whatsappStates={whatsappStates}
            onSendWhatsApp={sendWhatsAppMessage}
            onPreviewWhatsApp={previewWhatsAppMessage}
            paymentStates={paymentStates}
            onMarkPaid={markAsPaid}
            onMarkUnpaid={markAsUnpaid}
            onOpenPaymentModal={openPaymentModal}
          />

          {/* Salle 2 - Visible uniquement si elle a des patients */}
          {!isSalle2Empty && (
            <SalleColumn
              title="Salle 2"
              patients={salle2}
              color="green"
              salleId="salle2"
              onStart={startConsultation}
              onFinish={finishConsultation}
              onMarkAbsent={markAsAbsent}
              onMoveToSalle={updateAppointmentRoom}
              whatsappStates={whatsappStates}
              onSendWhatsApp={sendWhatsAppMessage}
              onPreviewWhatsApp={previewWhatsAppMessage}
              paymentStates={paymentStates}
              onMarkPaid={markAsPaid}
              onMarkUnpaid={markAsUnpaid}
              onOpenPaymentModal={openPaymentModal}
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

        {/* Modal de prévisualisation WhatsApp */}
        {showWhatsAppPreview && previewData && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <MessageCircle className="w-6 h-6 text-green-600" />
                    <h2 className="text-xl font-bold text-gray-900">Aperçu Message WhatsApp</h2>
                  </div>
                  <button
                    onClick={() => setShowWhatsAppPreview(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    ✕
                  </button>
                </div>

                {/* Informations patient */}
                <div className="bg-gray-50 p-3 rounded-lg mb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {previewData.appointment.patient.prenom} {previewData.appointment.patient.nom}
                      </h3>
                      <p className="text-sm text-gray-600">
                        📞 {previewData.appointment.patient.numero_whatsapp || previewData.appointment.patient.telephone}
                      </p>
                    </div>
                    <div className="text-right text-sm">
                      <div className="font-medium">{previewData.salle === 'salle1' ? 'Salle 1' : 'Salle 2'}</div>
                      <div className="text-gray-500">Position #{previewData.waitingTime.position}</div>
                    </div>
                  </div>
                </div>

                {/* Aperçu du message */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <div className="text-sm font-medium text-green-800 mb-2">Message à envoyer:</div>
                  <div className="bg-white p-3 rounded border text-sm whitespace-pre-wrap font-mono">
                    {previewData.message}
                  </div>
                </div>

                {/* Statistiques temps d'attente */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                  <div className="bg-blue-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-600">{previewData.waitingTime.minutes}</div>
                    <div className="text-xs text-blue-800">Minutes d'attente</div>
                  </div>
                  <div className="bg-orange-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-orange-600">{previewData.waitingTime.patientsAhead}</div>
                    <div className="text-xs text-orange-800">Patients avant</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowWhatsAppPreview(false)}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded-lg transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={confirmSendWhatsApp}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <Send className="w-4 h-4" />
                    <span>Envoyer</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DragDropContext>
  );
};

export default WaitingRoom;