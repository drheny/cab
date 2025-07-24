import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
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
  ChevronUp,
  ChevronDown,
  List,
  Grid,
  CheckCircle,
  Building2,
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
  Phone
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import AppointmentModal from './AppointmentModal';
import WhatsAppModal from './WhatsAppModal';

import PaymentModal from './PaymentModal';

// Backend URL from environment
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

const Calendar = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();
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
  
  // WhatsApp modal states
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [whatsappPatient, setWhatsappPatient] = useState(null);
  const [whatsappAppointment, setWhatsappAppointment] = useState(null);
  
  // Modal consultation states - Support multi-instances
  const [consultationModals, setConsultationModals] = useState(new Map());
  
  // Global timer (can be deprecated once per-modal timers are fully implemented)
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  
  // Données de la consultation - Maintenant par patient
  const [consultationDataMap, setConsultationDataMap] = useState(new Map());
  
  // Timers par modal de consultation
  const [consultationTimers, setConsultationTimers] = useState(new Map());
  
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

  // Memoized functions to prevent unnecessary re-renders
  const resetForm = useCallback(() => {
    setFormData({
      patient_id: '',
      date: selectedDate,
      heure: '',
      type_rdv: 'visite',
      motif: '',
      notes: ''
    });
    setSelectedAppointment(null);
  }, [selectedDate]);

  const openModal = useCallback((appointment = null) => {
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
  }, [resetForm]);

  const openModalWithDateTime = useCallback((dateTime = {}) => {
    resetForm();
    setFormData(prev => ({
      ...prev,
      date: dateTime.date || selectedDate,
      heure: dateTime.heure || ''
    }));
    setShowModal(true);
  }, [resetForm, selectedDate]);

  useEffect(() => {
    fetchData();
    
    // Auto-open modal from Dashboard quick action
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('action') === 'add') {
      openModal();
      window.history.replaceState({}, '', '/calendar');
    }
  }, [selectedDate, viewMode]); // openModal is defined later, will be handled by React

  // Gestion du chronomètre global (legacy)
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

  // Gestion des chronomètres individuels pour chaque modal de consultation
  useEffect(() => {
    const intervals = new Map();
    
    consultationTimers.forEach((timerData, appointmentId) => {
      if (timerData.isRunning) {
        const interval = setInterval(() => {
          setConsultationTimers(prev => {
            const newMap = new Map(prev);
            const currentTimer = newMap.get(appointmentId);
            if (currentTimer) {
              newMap.set(appointmentId, {
                ...currentTimer,
                seconds: currentTimer.seconds + 1
              });
            }
            return newMap;
          });
        }, 1000);
        intervals.set(appointmentId, interval);
      }
    });

    return () => {
      intervals.forEach(interval => clearInterval(interval));
    };
  }, [consultationTimers]);

  const fetchData = useCallback(async () => {
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
  }, [selectedDate, viewMode, API_BASE_URL]);

  const handleCreateAppointment = useCallback(async (appointmentData = null) => {
    try {
      const dataToSend = appointmentData || formData;
      const response = await axios.post(`${API_BASE_URL}/api/appointments`, dataToSend);
      toast.success('Rendez-vous créé avec succès');
      setShowModal(false);
      resetForm();
      await fetchData();
      return { success: true };
    } catch (error) {
      toast.error('Erreur lors de la création du rendez-vous: ' + (error.response?.data?.detail || error.message));
      return { success: false, error: error.response?.data?.detail || error.message };
    }
  }, [formData, API_BASE_URL, resetForm, fetchData]);

  const handleUpdateAppointment = useCallback(async () => {
    try {
      await axios.put(`${API_BASE_URL}/api/appointments/${selectedAppointment.id}`, formData);
      toast.success('Rendez-vous mis à jour avec succès');
      setShowModal(false);
      resetForm();
      await fetchData();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du rendez-vous');
    }
  }, [formData, selectedAppointment, API_BASE_URL, resetForm, fetchData]);

  const handleDeleteAppointment = useCallback(async (appointmentId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce rendez-vous ?')) return;

    setAppointments(prevAppointments => 
      prevAppointments.filter(apt => apt.id !== appointmentId)
    );

    try {
      await axios.delete(`${API_BASE_URL}/api/appointments/${appointmentId}`);
      toast.success('Rendez-vous supprimé avec succès');
    } catch (error) {
      toast.error('Erreur lors de la suppression du rendez-vous');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData]);

  const handleStatusUpdate = useCallback(async (appointmentId, newStatus) => {
    setAppointments(prevAppointments =>
      prevAppointments.map(apt => {
        if (apt.id === appointmentId) {
          const updatedApt = { ...apt, statut: newStatus };
          if (newStatus === 'attente') {
            updatedApt.heure_arrivee_attente = new Date().toISOString();
          }
          return updatedApt;
        }
        return apt;
      })
    );

    try {
      const updateData = { statut: newStatus };
      if (newStatus === 'attente') {
        updateData.heure_arrivee_attente = new Date().toISOString();
      }
      
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, updateData);
      toast.success('Statut mis à jour');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du statut');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData]);

  const handleTypeToggle = useCallback(async (appointmentId, currentType) => {
    const newType = currentType === 'visite' ? 'controle' : 'visite';
    
    setAppointments(prevAppointments => 
      prevAppointments.map(apt => 
        apt.id === appointmentId ? { ...apt, type_rdv: newType } : apt
      )
    );

    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}`, { type_rdv: newType });
      
      if (newType === 'controle') {
        setAppointments(prevAppointments => 
          prevAppointments.map(apt => 
            apt.id === appointmentId ? { ...apt, paye: false } : apt
          )
        );
        
        await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/paiement`, {
          paye: false,
          gratuit: true,
          montant: 0,
          methode_paiement: ''
        });
      }
      
      toast.success(`Type changé vers ${newType === 'visite' ? 'Visite' : 'Contrôle'}`);
    } catch (error) {
      toast.error('Erreur lors du changement de type');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData]);

  // Démarrer consultation (attente → en_cours)
  const handleStartConsultation = useCallback(async (appointmentId) => {
    // Calculer la durée d'attente avant le changement de statut
    const appointment = appointments.find(apt => apt.id === appointmentId);
    let dureeAttente = 0;
    
    if (appointment && appointment.heure_arrivee_attente) {
      const arriveeTime = new Date(appointment.heure_arrivee_attente);
      const currentTime = new Date();
      dureeAttente = Math.floor((currentTime - arriveeTime) / (1000 * 60)); // Durée en minutes
    }

    setAppointments(prevAppointments =>
      prevAppointments.map(apt =>
        apt.id === appointmentId ? { 
          ...apt, 
          statut: 'en_cours',
          duree_attente: dureeAttente 
        } : apt
      )
    );

    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { 
        statut: 'en_cours',
        duree_attente: dureeAttente
      });
      toast.success('Consultation démarrée');
    } catch (error) {
      toast.error('Erreur lors du démarrage de la consultation');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData, appointments]);

  // Fonctions pour gérer les modals de consultation multi-instances
  const ouvrirModalConsultation = (appointment) => {
    const appointmentId = appointment.id;
    const patientInfo = appointment.patient;
    
    // Créer une nouvelle instance de modal si elle n'existe pas
    if (!consultationModals.has(appointmentId)) {
      const newModal = {
        isOpen: true,
        isMinimized: false,
        appointmentId: appointmentId,
        patientInfo: patientInfo
      };
      
      setConsultationModals(prev => new Map(prev).set(appointmentId, newModal));
      
      // Initialiser les données de consultation pour ce patient s'il n'y en a pas
      if (!consultationDataMap.has(appointmentId)) {
        const initialData = {
          poids: '',
          taille: '',
          pc: '',
          temperature: '',
          observation_medicale: '',
          traitement: '',
          bilans: '',
          type_rdv: appointment.type_rdv || 'visite',
          motif: appointment.motif || '',
          notes: appointment.notes || ''
        };
        setConsultationDataMap(prev => new Map(prev).set(appointmentId, initialData));
      }
      
      // Initialiser le timer pour ce modal
      if (!consultationTimers.has(appointmentId)) {
        setConsultationTimers(prev => new Map(prev).set(appointmentId, {
          seconds: 0,
          isRunning: true // Démarrer automatiquement
        }));
      }
    } else {
      // Réactiver le modal existant
      setConsultationModals(prev => {
        const newMap = new Map(prev);
        const modal = newMap.get(appointmentId);
        newMap.set(appointmentId, { ...modal, isOpen: true, isMinimized: false });
        return newMap;
      });
    }
  };

  // Réduire le modal de consultation
  const reduireModalConsultation = (appointmentId) => {
    setConsultationModals(prev => {
      const newMap = new Map(prev);
      const modal = newMap.get(appointmentId);
      if (modal) {
        newMap.set(appointmentId, { ...modal, isMinimized: true });
      }
      return newMap;
    });
  };

  // Restaurer le modal de consultation
  const restaurerModalConsultation = (appointmentId) => {
    setConsultationModals(prev => {
      const newMap = new Map(prev);
      const modal = newMap.get(appointmentId);
      if (modal) {
        newMap.set(appointmentId, { ...modal, isMinimized: false });
      }
      return newMap;
    });
  };

  // Contrôler le timer d'un modal spécifique
  const toggleModalTimer = (appointmentId) => {
    setConsultationTimers(prev => {
      const newMap = new Map(prev);
      const currentTimer = newMap.get(appointmentId);
      if (currentTimer) {
        newMap.set(appointmentId, {
          ...currentTimer,
          isRunning: !currentTimer.isRunning
        });
      }
      return newMap;
    });
  };

  // Réinitialiser le timer d'un modal spécifique
  const resetModalTimer = (appointmentId) => {
    setConsultationTimers(prev => {
      const newMap = new Map(prev);
      const currentTimer = newMap.get(appointmentId);
      if (currentTimer) {
        newMap.set(appointmentId, {
          ...currentTimer,
          seconds: 0,
          isRunning: false
        });
      }
      return newMap;
    });
  };

  // Fermer le modal de consultation
  const fermerModalConsultation = (appointmentId) => {
    setConsultationModals(prev => {
      const newMap = new Map(prev);
      newMap.delete(appointmentId);
      return newMap;
    });
    
    // Arrêter le timer de ce modal
    setConsultationTimers(prev => {
      const newMap = new Map(prev);
      const currentTimer = newMap.get(appointmentId);
      if (currentTimer) {
        newMap.set(appointmentId, {
          ...currentTimer,
          isRunning: false
        });
      }
      return newMap;
    });
    
    // Garder les données pour une réouverture potentielle (ne pas supprimer consultationDataMap)
  };

  // Mettre à jour les données de consultation pour un patient spécifique
  const updateConsultationData = (appointmentId, field, value) => {
    setConsultationDataMap(prev => {
      const newMap = new Map(prev);
      const currentData = newMap.get(appointmentId) || {};
      newMap.set(appointmentId, { ...currentData, [field]: value });
      return newMap;
    });
  };

  // Sauvegarder la consultation pour un patient spécifique
  const sauvegarderConsultation = async (appointmentId) => {
    try {
      const appointment = appointments.find(a => a.id === appointmentId);
      const consultationData = consultationDataMap.get(appointmentId) || {};
      
      if (!appointment) {
        toast.error('Rendez-vous non trouvé');
        return;
      }

      // Helper function to safely get string values
      const safeString = (value) => {
        if (value === null || value === undefined) return '';
        return String(value).trim();
      };

      // Helper function to safely get numeric values
      const safeNumber = (value) => {
        if (value === null || value === undefined || value === '') return null;
        const num = parseFloat(value);
        return isNaN(num) ? null : num;
      };

      // Créer ou mettre à jour la consultation avec des valeurs sûres
      const consultationPayload = {
        patient_id: appointment.patient_id,
        appointment_id: appointmentId,
        date: appointment.date,
        type_rdv: safeString(consultationData.type_rdv || appointment.type_rdv || 'visite'),
        motif: safeString(consultationData.motif || appointment.motif || ''),
        poids: safeNumber(consultationData.poids),
        taille: safeNumber(consultationData.taille),
        pc: safeNumber(consultationData.pc),
        temperature: safeNumber(consultationData.temperature),
        observation_medicale: safeString(consultationData.observation_medicale),
        traitement: safeString(consultationData.traitement),
        bilans: safeString(consultationData.bilans),
        notes: safeString(consultationData.notes),
        relance_telephonique: Boolean(consultationData.relance_telephonique),
        date_relance: consultationData.date_relance || null
      };

      console.log('Saving consultation with payload:', consultationPayload);

      // Sauvegarder la consultation
      const consultationResponse = await axios.post(`${API_BASE_URL}/api/consultations`, consultationPayload);
      console.log('Consultation saved:', consultationResponse.data);

      // Mettre à jour le statut du RDV à "terminé"
      const statusResponse = await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, {
        statut: 'termine'
      });
      console.log('Status updated:', statusResponse.data);

      toast.success('Consultation sauvegardée avec succès');
      fermerModalConsultation(appointmentId);
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error saving consultation:', error);
      console.error('Error response:', error.response);
      
      // Améliorer la gestion d'erreur pour éviter [object Object]
      let errorMessage = 'Erreur lors de la sauvegarde de la consultation';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(item => 
              typeof item === 'string' ? item : item.msg || JSON.stringify(item)
            ).join(', ');
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else {
          // Tenter d'extraire un message lisible de l'objet d'erreur
          errorMessage = Object.keys(errorData).map(key => 
            `${key}: ${errorData[key]}`
          ).join(', ');
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(`Erreur: ${errorMessage}`);
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

  // Marquer patient en salle d'attente avec timestamp
  const handlePatientToWaitingRoom = useCallback(async (appointmentId) => {
    try {
      const currentTime = new Date().toISOString();
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { 
        statut: 'attente',
        heure_arrivee_attente: currentTime
      });
      toast.success('Patient en salle d\'attente');
      await fetchData();
    } catch (error) {
      toast.error('Erreur lors de la mise en salle d\'attente');
    }
  }, [API_BASE_URL, fetchData]);

  // Terminer consultation (en_cours → termine)
  const handleFinishConsultation = useCallback(async (appointmentId) => {
    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/statut`, { statut: 'termine' });
      toast.success('Consultation terminée');
      await fetchData();
    } catch (error) {
      toast.error('Erreur lors de la finalisation de la consultation');
    }
  }, [API_BASE_URL, fetchData]);

  // Gestion des paiements avec nouveau modal
  const handleOpenPaymentModal = useCallback((appointment) => {
    setSelectedPaymentAppointment(appointment);
    setShowPaymentModal(true);
  }, []);

  const handleClosePaymentModal = useCallback(() => {
    setShowPaymentModal(false);
    setSelectedPaymentAppointment(null);
  }, []);

  // Gestion des paiements
  const handlePaymentUpdate = useCallback(async (appointmentId, paymentData) => {
    setAppointments(prevAppointments =>
      prevAppointments.map(apt =>
        apt.id === appointmentId ? { ...apt, paye: paymentData.paye } : apt
      )
    );

    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/paiement`, paymentData);
      toast.success('Paiement mis à jour');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du paiement');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData]);

  // Patient reordering with CORRECT optimistic updates - no page refresh
  const handlePatientReorder = useCallback(async (appointmentId, action) => {
    console.log(`\n=== ARROW CLICK: ${action} ===`);
    
    // Get current waiting patients sorted by priority
    const waitingPatients = appointments
      .filter(apt => apt.statut === 'attente')
      .sort((a, b) => {
        const priorityA = typeof a.priority === 'number' ? a.priority : 999;
        const priorityB = typeof b.priority === 'number' ? b.priority : 999;
        return priorityA - priorityB;
      });
    
    if (waitingPatients.length < 2) return;
    
    // Find current position in sorted array
    const currentIndex = waitingPatients.findIndex(apt => apt.id === appointmentId);
    if (currentIndex === -1) return;
    
    // Calculate new position
    let newIndex = currentIndex;
    if (action === 'move_up' && currentIndex > 0) {
      newIndex = currentIndex - 1;
    } else if (action === 'move_down' && currentIndex < waitingPatients.length - 1) {
      newIndex = currentIndex + 1;
    } else {
      return; // No movement possible
    }
    
    console.log(`Moving from position ${currentIndex} to ${newIndex}`);
    
    // OPTIMISTIC UPDATE - mirrors exact backend logic
    setAppointments(prevAppointments => {
      const otherAppointments = prevAppointments.filter(apt => apt.statut !== 'attente');
      
      // Reorder the waiting patients array
      const newWaitingOrder = [...waitingPatients];
      const [movedPatient] = newWaitingOrder.splice(currentIndex, 1);
      newWaitingOrder.splice(newIndex, 0, movedPatient);
      
      // Update priorities to match new order (0-based)
      const updatedWaitingPatients = newWaitingOrder.map((apt, index) => ({
        ...apt,
        priority: index
      }));
      
      console.log('Optimistic update:', updatedWaitingPatients.map(p => `${p.patient?.nom} (priority: ${p.priority})`));
      
      return [...updatedWaitingPatients, ...otherAppointments];
    });
    
    // Call backend API (no await fetchData - keep optimistic update)
    try {
      const response = await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/priority`, { action });
      console.log('Backend response:', response.data);
      toast.success('Patient repositionné');
      
      // NO fetchData() call - optimistic update is correct
      
    } catch (error) {
      console.error('Error during reordering:', error);
      toast.error('Erreur lors du repositionnement');
      
      // Only refresh on error to revert optimistic update
      await fetchData();
    }
  }, [API_BASE_URL, fetchData, appointments]);

  const handleRoomAssignment = useCallback(async (appointmentId, newRoom) => {
    setAppointments(prevAppointments =>
      prevAppointments.map(apt =>
        apt.id === appointmentId ? { ...apt, salle: newRoom } : apt
      )
    );

    try {
      await axios.put(`${API_BASE_URL}/api/rdv/${appointmentId}/salle?salle=${newRoom}`);
      const roomText = newRoom === '' ? 'Aucune salle' : 
                      newRoom === 'salle1' ? 'Salle 1' : 'Salle 2';
      toast.success(`Patient assigné à: ${roomText}`);
    } catch (error) {
      toast.error('Erreur lors de l\'assignation de salle');
      await fetchData();
    }
  }, [API_BASE_URL, fetchData]);

  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPaymentAppointment, setSelectedPaymentAppointment] = useState(null);

  const viewPatientDetails = useCallback(async (patientId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients/${patientId}`);
      setSelectedPatient(response.data);
      setShowPatientModal(true);
    } catch (error) {
      toast.error('Erreur lors du chargement des détails du patient');
    }
  }, [API_BASE_URL, setSelectedPatient, setShowPatientModal]);

  const navigateDate = useCallback((direction) => {
    const currentDate = new Date(selectedDate);
    if (direction === 'prev') {
      currentDate.setDate(currentDate.getDate() - 1);
    } else {
      currentDate.setDate(currentDate.getDate() + 1);
    }
    setSelectedDate(currentDate.toISOString().split('T')[0]);
  }, [selectedDate]);

  // Memoized utility functions
  const getStatusColor = useCallback((status) => {
    switch (status) {
      case 'absent': return 'bg-gray-100 text-gray-800';
      case 'attente': return 'bg-yellow-100 text-yellow-800';
      case 'en_cours': return 'bg-blue-100 text-blue-800';
      case 'termine': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, []);

  const getStatusText = useCallback((status) => {
    switch (status) {
      case 'absent': return 'Absent';
      case 'attente': return 'En attente';
      case 'en_cours': return 'En cours';
      case 'termine': return 'Terminé';
      default: return 'Absent';
    }
  }, []);

  const getWhatsAppLink = useCallback((phone) => {
    const cleanPhone = phone.replace(/\D/g, '');
    return `https://wa.me/212${cleanPhone.startsWith('0') ? cleanPhone.substring(1) : cleanPhone}`;
  }, []);

  // WhatsApp Modal Functions
  const openWhatsAppModal = useCallback((patient, appointment = null) => {
    if (!patient.numero_whatsapp) {
      toast.error('Patient n\'a pas de numéro WhatsApp');
      return;
    }
    
    setWhatsappPatient(patient);
    setWhatsappAppointment(appointment);
    setShowWhatsAppModal(true);
  }, []);

  const closeWhatsAppModal = useCallback(() => {
    setShowWhatsAppModal(false);
    setWhatsappPatient(null);
    setWhatsappAppointment(null);
  }, []);

  const formatDate = useCallback((dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }, []);

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
      
      // For waiting room patients, sort by priority field (handle null values)
      if (a.statut === 'attente' && b.statut === 'attente') {
        const priorityA = typeof a.priority === 'number' ? a.priority : 999;
        const priorityB = typeof b.priority === 'number' ? b.priority : 999;
        
        // If both have null priority, sort by appointment ID for consistency
        if (priorityA === 999 && priorityB === 999) {
          return a.id.localeCompare(b.id);
        }
        
        const priorityDiff = priorityA - priorityB;
        if (priorityDiff !== 0) return priorityDiff;
      }
      
      // Then by time for other cases
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

      {/* List View - Workflow Optimisé - Sections réorganisées */}
      {viewMode === 'list' && (
        <div className="space-y-6">
          {/* 1. Salle d'attente (en haut) */}
          <WorkflowSection
            title="🟢 Salle d'attente"
            appointments={groupedAppointments.attente}
            sectionType="attente"
            onStatusUpdate={handleStatusUpdate}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onStartConsultation={handleStartConsultation}
            onRoomAssignment={handleRoomAssignment}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            onPatientReorder={handlePatientReorder}
            onOpenPaymentModal={handleOpenPaymentModal}
            onWhatsApp={openWhatsAppModal}
            user={user}
          />
          
          {/* 2. RDV Programmés */}
          <WorkflowSection
            title="📅 RDV Programmés"
            appointments={groupedAppointments.absent}
            sectionType="absent"
            onStatusUpdate={handleStatusUpdate}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            onOpenPaymentModal={handleOpenPaymentModal}
            onWhatsApp={openWhatsAppModal}
            user={user}
          />
          
          {/* 3. En retard */}
          <WorkflowSection
            title="🟠 En retard"
            appointments={groupedAppointments.retard}
            sectionType="retard"
            onStatusUpdate={handleStatusUpdate}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onStartConsultation={handleStartConsultation}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            onOpenPaymentModal={handleOpenPaymentModal}
            onWhatsApp={openWhatsAppModal}
            user={user}
          />
          
          {/* 4. En consultation */}
          <WorkflowSection
            title="🔵 En consultation"
            appointments={groupedAppointments.en_cours}
            sectionType="en_cours"
            onStatusUpdate={handleStatusUpdate}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onFinishConsultation={handleFinishConsultation}
            onOpenConsultation={ouvrirModalConsultation}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            onOpenPaymentModal={handleOpenPaymentModal}
            onWhatsApp={openWhatsAppModal}
            user={user}
          />
          
          {/* 5. Terminé (en bas) */}
          <WorkflowSection
            title="✅ Terminé"
            appointments={groupedAppointments.termine}
            sectionType="termine"
            onStatusUpdate={handleStatusUpdate}
            onTypeToggle={handleTypeToggle}
            onPaymentUpdate={handlePaymentUpdate}
            onEdit={openModal}
            onDelete={handleDeleteAppointment}
            onViewPatient={viewPatientDetails}
            onOpenPaymentModal={handleOpenPaymentModal}
            onWhatsApp={openWhatsAppModal}
            isCompleted={true}
            user={user}
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
          onEdit={openModal}
          onDelete={handleDeleteAppointment}
          onViewPatient={viewPatientDetails}
          onCreateAppointment={openModalWithDateTime}
          onOpenPaymentModal={handleOpenPaymentModal}
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

      {/* Multi-Instance Consultation Modals */}
      {Array.from(consultationModals.entries()).map(([appointmentId, modal]) => {
        const currentConsultationData = consultationDataMap.get(appointmentId) || {};
        const currentTimer = consultationTimers.get(appointmentId) || { seconds: 0, isRunning: false };
        
        return (
          <div key={appointmentId}>
            {modal.isOpen && (
              <>
                {/* Modal réduit */}
                {modal.isMinimized ? (
                  <div className="fixed bottom-4 right-4 z-50" style={{ right: `${16 + (Array.from(consultationModals.keys()).indexOf(appointmentId) * 320)}px` }}>
                    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[300px]">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Clock className="w-5 h-5 text-blue-600" />
                          <span className="font-medium text-gray-900">
                            {modal.patientInfo?.prenom} {modal.patientInfo?.nom}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-lg font-mono text-blue-600">
                            {formatTimer(currentTimer.seconds)}
                          </span>
                          <button
                            onClick={() => restaurerModalConsultation(appointmentId)}
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
                              Consultation - {modal.patientInfo?.prenom} {modal.patientInfo?.nom}
                            </h2>
                            <p className="text-gray-600">
                              {new Date().toLocaleDateString('fr-FR')} - {formatTimer(currentTimer.seconds)}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => reduireModalConsultation(appointmentId)}
                              className="p-2 hover:bg-gray-100 rounded-lg"
                            >
                              <Minimize2 className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => fermerModalConsultation(appointmentId)}
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
                                Durée: {formatTimer(currentTimer.seconds)}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => toggleModalTimer(appointmentId)}
                                className={`p-2 rounded-lg ${
                                  currentTimer.isRunning 
                                    ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                                    : 'bg-green-100 text-green-600 hover:bg-green-200'
                                }`}
                              >
                                {currentTimer.isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                              </button>
                              <button
                                onClick={() => resetModalTimer(appointmentId)}
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
                          sauvegarderConsultation(appointmentId);
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
                                    value={currentConsultationData.poids || ''}
                                    onChange={(e) => updateConsultationData(appointmentId, 'poids', e.target.value)}
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
                                    value={currentConsultationData.taille || ''}
                                    onChange={(e) => updateConsultationData(appointmentId, 'taille', e.target.value)}
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
                                    value={currentConsultationData.pc || ''}
                                    onChange={(e) => updateConsultationData(appointmentId, 'pc', e.target.value)}
                                    className="input-field"
                                    placeholder="0"
                                  />
                                </div>
                              </div>
                            </div>

                            {/* Observations cliniques - Full width pour iPad/stylet */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Observation clinique
                              </label>
                              <textarea
                                value={currentConsultationData.observation_medicale || ''}
                                onChange={(e) => updateConsultationData(appointmentId, 'observation_medicale', e.target.value)}
                                className="input-field textarea-stylus"
                                rows="5"
                                placeholder="Observations du médecin... (Optimisé pour Apple Pencil)"
                              />
                            </div>

                            {/* Traitement - Full width pour iPad/stylet */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Traitements
                              </label>
                              <textarea
                                value={currentConsultationData.traitement || ''}
                                onChange={(e) => updateConsultationData(appointmentId, 'traitement', e.target.value)}
                                className="input-field textarea-stylus"
                                rows="5"
                                placeholder="Traitement prescrit... (Optimisé pour Apple Pencil)"
                              />
                            </div>

                            {/* Bilans - Full width pour iPad/stylet */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Bilans
                              </label>
                              <textarea
                                value={currentConsultationData.bilans || ''}
                                onChange={(e) => updateConsultationData(appointmentId, 'bilans', e.target.value)}
                                className="input-field textarea-stylus"
                                rows="4"
                                placeholder="Bilans demandés... (Optimisé pour Apple Pencil)"
                              />
                            </div>

                            {/* Relance téléphonique */}
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-4">Relance téléphonique</h3>
                              <div className="flex items-center space-x-4">
                                <label className="flex items-center space-x-2">
                                  <input
                                    type="checkbox"
                                    checked={currentConsultationData.relance_telephonique || false}
                                    onChange={(e) => updateConsultationData(appointmentId, 'relance_telephonique', e.target.checked)}
                                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                  />
                                  <span className="text-sm font-medium text-gray-700">
                                    <Phone className="w-4 h-4 inline mr-1" />
                                    Programmer une relance
                                  </span>
                                </label>
                                {currentConsultationData.relance_telephonique && (
                                  <div>
                                    <input
                                      type="date"
                                      value={currentConsultationData.date_relance || ''}
                                      onChange={(e) => updateConsultationData(appointmentId, 'date_relance', e.target.value)}
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
                              onClick={() => fermerModalConsultation(appointmentId)}
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
      })}

      {/* Payment Modal */}
      {showPaymentModal && selectedPaymentAppointment && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={handleClosePaymentModal}
          appointment={selectedPaymentAppointment}
          onPaymentUpdate={handlePaymentUpdate}
          API_BASE_URL={API_BASE_URL}
          user={user}
        />
      )}
    </div>
  );
};

// Composant WeekView pour la vue semaine
const WeekView = ({ 
  weekData, 
  onStatusUpdate, 
  onRoomAssignment, 
  onEdit, 
  onDelete, 
  onViewPatient, 
  selectedDate, 
  onCreateAppointment, 
  onOpenPaymentModal 
}) => {
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

  const getAppointmentColor = (appointment) => {
    // Couleur rouge pour les retards
    if (appointment.statut === 'retard') {
      return 'bg-red-100 text-red-800 border-red-200';
    }
    
    // Couleur selon le type de RDV
    switch (appointment.type_rdv) {
      case 'visite': return 'bg-green-100 text-green-800 border-green-200';
      case 'controle': return 'bg-blue-100 text-blue-800 border-blue-200';
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
                            className={`text-xs p-1 rounded border cursor-pointer hover:shadow-sm transition-all relative ${getAppointmentColor(apt)}`}
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
                                apt.type_rdv === 'visite' ? 'bg-green-200 text-green-800' : 'bg-blue-200 text-blue-800'
                              }`}>
                                {apt.type_rdv === 'visite' ? 'V' : 'C'}
                              </span>
                              {apt.salle && (
                                <span className="px-1 py-0.5 rounded text-xs bg-purple-200 text-purple-800">
                                  {apt.salle === 'salle1' ? 'S1' : 'S2'}
                                </span>
                              )}
                              {/* Badge de paiement - Cliquable */}
                              <button 
                                className={`px-1 py-0.5 rounded text-xs cursor-pointer hover:opacity-80 transition-opacity ${
                                  apt.type_rdv === 'controle' 
                                    ? 'bg-green-200 text-green-800' 
                                    : apt.paye 
                                      ? 'bg-green-200 text-green-800' 
                                      : 'bg-red-200 text-red-800'
                                }`}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onOpenPaymentModal(apt);
                                }}
                                title="Cliquer pour gérer le paiement"
                              >
                                {apt.type_rdv === 'controle' ? 'Gratuit' : apt.paye ? 'Payé' : 'Non Payé'}
                              </button>
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
  onTypeToggle,
  onPaymentUpdate,
  onStartConsultation,
  onFinishConsultation,
  onOpenConsultation,
  onRoomAssignment,
  onEdit, 
  onDelete, 
  onViewPatient,
  onPatientReorder,
  onOpenPaymentModal,
  isCompleted = false,
  user
}) => {
  const getSectionColor = () => {
    switch (sectionType) {
      case 'attente': return 'border-green-200 bg-green-50';
      case 'en_cours': return 'border-blue-200 bg-blue-50';
      case 'absent': return 'border-blue-200 bg-blue-50'; // RDV Programmés en bleu
      case 'retard': return 'border-orange-200 bg-orange-50';
      case 'termine': return 'border-gray-200 bg-gray-50';
      default: return 'border-gray-200 bg-white';
    }
  };

  return (
    <div className={`rounded-xl shadow-sm border-2 ${getSectionColor()} ${isCompleted ? 'opacity-75' : ''}`}>
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600">
          {appointments.length} patient(s)
          {sectionType === 'attente' && appointments.length > 1 && <span className="text-gray-400 ml-2">• Utilisez les flèches pour réorganiser</span>}
        </p>
      </div>
      
      {/* Simple list without drag and drop */}
      <div className="divide-y divide-gray-100">
        {appointments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">👥</div>
            <p>Aucun patient dans cette section</p>
          </div>
        ) : (
          appointments.map((appointment, index) => (
            <WorkflowCard
              key={appointment.id}
              appointment={appointment}
              index={index}
              totalCount={appointments.length}
              sectionType={sectionType}
              onStatusUpdate={onStatusUpdate}
              onTypeToggle={onTypeToggle}
              onPaymentUpdate={onPaymentUpdate}
              onStartConsultation={onStartConsultation}
              onFinishConsultation={onFinishConsultation}
              onOpenConsultation={onOpenConsultation}
              onRoomAssignment={onRoomAssignment}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewPatient={onViewPatient}
              onPatientReorder={onPatientReorder}
              onOpenPaymentModal={onOpenPaymentModal}
              isCompleted={isCompleted}
              user={user}
            />
          ))
        )}
      </div>
    </div>
  );
};

// Composant WorkflowCard optimisé avec badges interactifs
const WorkflowCard = React.memo(({ 
  appointment, 
  index,
  totalCount,
  sectionType,
  onStatusUpdate, 
  onTypeToggle,
  onPaymentUpdate,
  onStartConsultation,
  onFinishConsultation,
  onOpenConsultation,
  onRoomAssignment,
  onEdit, 
  onDelete, 
  onViewPatient,
  onPatientReorder,
  onOpenPaymentModal,
  isCompleted,
  user
}) => {
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [waitingTime, setWaitingTime] = useState(0);

  // Fermer les dropdowns en cliquant à l'extérieur
  useEffect(() => {
    const handleClickOutside = () => {
      setShowStatusDropdown(false);
    };

    if (showStatusDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showStatusDropdown]);

  // Calculer temps d'attente pour patients en salle d'attente seulement
  useEffect(() => {
    if (sectionType === 'attente' && appointment.statut === 'attente') {
      // Le compteur se base sur l'heure d'arrivée en salle d'attente
      // Si pas d'heure d'arrivée spécifique, utiliser l'heure actuelle comme début
      const arrivalTime = appointment.heure_arrivee_attente || new Date().toISOString();
      const startTime = new Date(arrivalTime);
      const now = new Date();
      const diffMinutes = Math.max(0, Math.floor((now - startTime) / 60000));
      setWaitingTime(diffMinutes);
      
      // Mettre à jour toutes les minutes
      const interval = setInterval(() => {
        const newNow = new Date();
        const newDiffMinutes = Math.max(0, Math.floor((newNow - startTime) / 60000));
        setWaitingTime(newDiffMinutes);
      }, 60000);
      
      return () => clearInterval(interval);
    }
  }, [sectionType, appointment.statut, appointment.heure_arrivee_attente]);

  // Fonction pour obtenir le style du marqueur d'attente selon la durée
  const getWaitingTimeStyle = (minutes) => {
    if (minutes < 15) {
      return {
        bgColor: 'bg-green-100',
        textColor: 'text-green-700',
        iconColor: 'text-green-500',
        borderColor: 'border-green-200'
      };
    } else if (minutes < 30) {
      return {
        bgColor: 'bg-orange-100',
        textColor: 'text-orange-700',
        iconColor: 'text-orange-500',
        borderColor: 'border-orange-200'
      };
    } else {
      return {
        bgColor: 'bg-red-100',
        textColor: 'text-red-700',
        iconColor: 'text-red-500',
        borderColor: 'border-red-200'
      };
    }
  };

  // Fonction pour formatter la durée d'attente stockée
  const formatStoredWaitingTime = (minutes) => {
    if (!minutes || minutes === 0) return null;
    if (minutes === 1) return '1 min d\'attente';
    if (minutes < 60) return `${minutes} min d\'attente`;
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) {
      return hours === 1 ? '1h d\'attente' : `${hours}h d\'attente`;
    } else {
      return `${hours}h ${remainingMinutes}min d\'attente`;
    }
  };

  // Fonction pour obtenir le style de la durée d'attente stockée
  const getStoredWaitingTimeStyle = (minutes) => {
    if (!minutes) return null;
    
    if (minutes < 15) {
      return {
        bgColor: 'bg-green-50',
        textColor: 'text-green-600',
        borderColor: 'border-green-200'
      };
    } else if (minutes < 30) {
      return {
        bgColor: 'bg-orange-50',
        textColor: 'text-orange-600',
        borderColor: 'border-orange-200'
      };
    } else {
      return {
        bgColor: 'bg-red-50',
        textColor: 'text-red-600',
        borderColor: 'border-red-200'
      };
    }
  };

  // Fonction pour formatter la durée d'attente
  const formatWaitingTime = (minutes) => {
    if (minutes === 0) return 'Vient d\'arriver';
    if (minutes === 1) return '1 minute';
    if (minutes < 60) return `${minutes} minutes`;
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) {
      return hours === 1 ? '1 heure' : `${hours} heures`;
    } else {
      return `${hours}h ${remainingMinutes}min`;
    }
  };

  const getWhatsAppLink = (numero) => {
    if (!numero) return '#';
    const cleanNumber = numero.replace(/\D/g, '');
    return `https://wa.me/${cleanNumber}`;
  };

  const handleStatusChange = (newStatus) => {
    onStatusUpdate(appointment.id, newStatus);
    setShowStatusDropdown(false);
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

  const getRoomDisplayText = (salle) => {
    if (!salle || salle === '') return '';
    return salle === 'salle1' ? 'S1' : 'S2';
  };

  const getRoomColor = (salle) => {
    if (!salle || salle === '') return 'bg-gray-100 text-gray-600';
    return salle === 'salle1' ? 'bg-purple-100 text-purple-800' : 'bg-orange-100 text-orange-800';
  };

  // Fonction pour déterminer si le paiement peut être modifié par la secrétaire
  const canSecretaryModifyPayment = () => {
    // Si l'utilisateur est médecin, il peut toujours modifier
    if (user?.role === 'medecin') {
      return true;
    }
    
    // Si l'utilisateur est secrétaire
    if (user?.role === 'secretaire') {
      // Si la consultation n'est pas terminée, la secrétaire peut modifier
      if (appointment?.statut !== 'termine') {
        return true;
      }
      
      // Si la consultation est terminée, vérifier le statut de paiement
      if (appointment?.statut === 'termine') {
        // Si c'est un contrôle, toujours non modifiable (gratuit)
        if (appointment?.type_rdv === 'controle') {
          return false;
        }
        
        // Pour les visites terminées :
        // - Si "non payé", la secrétaire peut encore modifier
        // - Si "payé" ou autre statut défini, la secrétaire ne peut plus modifier
        return !appointment?.paye;
      }
    }
    
    // Par défaut, autoriser la modification
    return true;
  };

  const paymentStatus = getPaymentStatus();
  const canModifyPayment = canSecretaryModifyPayment();

  return (
    <div className="p-4 hover:bg-white/50 transition-colors">
      <div className="flex items-center justify-between">
        {/* Partie gauche - Info patient */}
        <div className="flex items-center space-x-4 flex-1">
          {/* Reorder buttons - SIMPLIFIED: Position-based logic */}
          {sectionType === 'attente' && totalCount > 1 && onPatientReorder && (
            <div className="flex flex-col space-y-1">
              <button
                onClick={() => {
                  console.log(`UP ARROW: ${appointment.patient?.nom} (position: ${index + 1}/${totalCount})`);
                  onPatientReorder(appointment.id, 'move_up');
                }}
                disabled={index === 0}
                className={`p-1 rounded text-xs ${
                  index === 0 
                    ? 'text-gray-300 cursor-not-allowed' 
                    : 'text-blue-500 hover:text-blue-700 hover:bg-blue-50'
                }`}
                title={`Monter d'un rang (${index + 1}/${totalCount})`}
              >
                <ChevronUp className="w-3 h-3" />
              </button>
              <button
                onClick={() => {
                  console.log(`DOWN ARROW: ${appointment.patient?.nom} (position: ${index + 1}/${totalCount})`);
                  onPatientReorder(appointment.id, 'move_down');
                }}
                disabled={index === totalCount - 1}
                className={`p-1 rounded text-xs ${
                  index === totalCount - 1 
                    ? 'text-gray-300 cursor-not-allowed' 
                    : 'text-blue-500 hover:text-blue-700 hover:bg-blue-50'
                }`}
                title={`Descendre d'un rang (${index + 1}/${totalCount})`}
              >
                <ChevronDown className="w-3 h-3" />
              </button>
            </div>
          )}
          
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
            
            {/* Marqueur d'attente raffiné pour patients en attente */}
            {sectionType === 'attente' && (
              <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border mt-1 ${
                getWaitingTimeStyle(waitingTime).bgColor
              } ${getWaitingTimeStyle(waitingTime).textColor} ${getWaitingTimeStyle(waitingTime).borderColor}`}>
                <Clock className={`w-3 h-3 ${getWaitingTimeStyle(waitingTime).iconColor}`} />
                <span>{formatWaitingTime(waitingTime)}</span>
                <span className="text-gray-500">d'attente</span>
              </div>
            )}

            {/* Marqueur durée d'attente stockée pour patients en cours et terminés */}
            {(sectionType === 'en_cours' || sectionType === 'termine') && appointment.duree_attente && (
              <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border mt-1 ${
                getStoredWaitingTimeStyle(appointment.duree_attente).bgColor
              } ${getStoredWaitingTimeStyle(appointment.duree_attente).textColor} ${getStoredWaitingTimeStyle(appointment.duree_attente).borderColor}`}>
                <Clock className="w-3 h-3 mr-1" />
                <span>{formatStoredWaitingTime(appointment.duree_attente)}</span>
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
              onClick={(e) => {
                e.stopPropagation();
                setShowStatusDropdown(!showStatusDropdown);
              }}
              className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200 transition-colors cursor-pointer"
              title="Cliquer pour changer le statut"
            >
              {appointment.statut}
            </button>
            
            {showStatusDropdown && (
              <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 min-w-[120px]">
                {['attente', 'en_cours', 'termine', 'absent'].map(status => (
                  <button
                    key={status}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStatusChange(status);
                    }}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors"
                  >
                    {status}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Badge Paiement - Cliquable pour modal avec restrictions de sécurité */}
          <button
            onClick={() => canModifyPayment ? onOpenPaymentModal(appointment) : null}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              canModifyPayment 
                ? 'cursor-pointer hover:opacity-80' 
                : 'cursor-not-allowed opacity-60'
            } ${paymentStatus.color} ${
              !canModifyPayment ? 'border-2 border-gray-400' : ''
            }`}
            title={
              canModifyPayment 
                ? "Cliquer pour gérer le paiement" 
                : user?.role === 'secretaire' 
                  ? "Paiement verrouillé - Seul le médecin peut modifier après paiement défini" 
                  : "Cliquer pour gérer le paiement"
            }
            disabled={!canModifyPayment}
          >
            {paymentStatus.text}
            {!canModifyPayment && user?.type === 'secretaire' && (
              <span className="ml-1 text-gray-600">🔒</span>
            )}
          </button>

          {/* Dropdown Salle - Pour patients en attente */}
          {sectionType === 'attente' && (
            <div className="relative">
              <select
                value={appointment.salle || ''}
                onChange={(e) => onRoomAssignment(appointment.id, e.target.value)}
                className="px-2 py-1 rounded text-xs font-medium border border-gray-300 bg-white hover:bg-gray-50 transition-colors cursor-pointer"
                title="Sélectionner une salle"
              >
                <option value="">Aucune salle</option>
                <option value="salle1">Salle 1</option>
                <option value="salle2">Salle 2</option>
              </select>
            </div>
          )}

          {/* Affichage salle pour autres sections */}
          {sectionType !== 'attente' && appointment.salle && (
            <span className={`px-2 py-1 rounded text-xs font-medium ${getRoomColor(appointment.salle)}`}>
              {getRoomDisplayText(appointment.salle)}
            </span>
          )}

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

          {/* Bouton Consultation pour patients en cours */}
          {sectionType === 'en_cours' && (
            <button
              onClick={() => onOpenConsultation(appointment)}
              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded font-medium transition-colors"
              title="Ouvrir la consultation"
            >
              Consultation
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
          user={user}
        />
      )}
    </div>
  );
});

export default Calendar;