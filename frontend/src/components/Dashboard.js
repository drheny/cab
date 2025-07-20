import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Calendar, 
  Clock, 
  DollarSign, 
  MessageCircle,
  Phone,
  AlertCircle,
  Gift,
  PhoneCall,
  Eye,
  X,
  MessageSquare
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Dashboard = ({ user }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_rdv: 0,
    rdv_restants: 0,
    rdv_attente: 0,
    rdv_en_cours: 0,
    rdv_termines: 0,
    recette_jour: 0,
    total_patients: 0,
    duree_attente_moyenne: 0
  });
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  
  // Data states
  const [birthdays, setBirthdays] = useState([]);
  const [phoneReminders, setPhoneReminders] = useState([]);
  
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';
  
  const [messages] = useState([
    {
      id: 1,
      type: 'anniversaire',
      titre: 'Anniversaire',
      patient: 'Lina Alami',
      patient_id: 'patient2',
      message: 'Anniversaire aujourd\'hui - 6 ans',
      time: '00:00',
      urgent: false
    },
    {
      id: 2,
      type: 'relance',
      titre: 'Relance téléphonique',
      patient: 'Omar Tazi',
      patient_id: 'patient3',
      message: 'Relance programmée pour contrôle',
      time: '10:00',
      urgent: false
    },
    {
      id: 3,
      type: 'retard',
      titre: 'Patient en retard',
      patient: 'Yassine Ben Ahmed',
      patient_id: 'patient1',
      message: 'RDV 09:00 - Non arrivé (retard 30 min)',
      time: '09:30',
      urgent: true
    }
  ]);

  const handleAddPatient = () => {
    // Naviguer vers la page patients avec un paramètre pour ouvrir le modal
    navigate('/patients?action=add');
  };

  const handleNewAppointment = () => {
    // Naviguer vers la page calendrier avec un paramètre pour ouvrir le modal
    navigate('/calendar?action=add');
  };

  const handlePhoneReminders = () => {
    // Afficher une notification avec les rappels téléphoniques
    toast.success('Rappels téléphoniques : 2 patients à contacter aujourd\'hui');
    // Optionnel: naviguer vers une page spécifique
    // navigate('/patients?filter=reminders');
  };

  useEffect(() => {
    fetchDashboardData();
    fetchBirthdays();
    fetchPhoneReminders();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const fetchBirthdays = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard/birthdays`);
      setBirthdays(response.data.birthdays || []);
    } catch (error) {
      console.error('Error fetching birthdays:', error);
    }
  };

  const fetchPhoneReminders = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard/phone-reminders`);
      setPhoneReminders(response.data.reminders || []);
    } catch (error) {
      console.error('Error fetching phone reminders:', error);
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

  const viewConsultationDetails = async (consultationId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/consultations/${consultationId}`);
      setSelectedConsultation(response.data);
      setShowConsultationModal(true);
    } catch (error) {
      console.error('Error fetching consultation details:', error);
      toast.error('Erreur lors du chargement des détails de la consultation');
    }
  };

  const sendWhatsAppBirthday = (patient) => {
    if (patient.numero_whatsapp) {
      const message = `Joyeux anniversaire ${patient.prenom} ! 🎉 Nous vous souhaitons une merveilleuse journée pour vos ${patient.age} ans. L'équipe du cabinet vous adresse ses meilleurs vœux ! 🎂`;
      const whatsappUrl = `https://wa.me/${patient.numero_whatsapp}?text=${encodeURIComponent(message)}`;
      window.open(whatsappUrl, '_blank');
    } else {
      toast.error('Numéro WhatsApp non disponible pour ce patient');
    }
  };

  const sendWhatsAppReminder = (reminder) => {
    if (reminder.numero_whatsapp) {
      const message = `Bonjour ${reminder.patient_prenom}, nous vous contactons pour le suivi de votre consultation du ${new Date(reminder.date_rdv).toLocaleDateString('fr-FR')}. Merci de nous rappeler pour planifier votre prochain rendez-vous si nécessaire.`;
      const whatsappUrl = `https://wa.me/${reminder.numero_whatsapp}?text=${encodeURIComponent(message)}`;
      window.open(whatsappUrl, '_blank');
    } else {
      toast.error('Numéro WhatsApp non disponible pour ce patient');
    }
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );

  const MessageCard = ({ message }) => {
    const getIcon = () => {
      switch (message.type) {
        case 'anniversaire':
          return <Gift className="w-4 h-4 text-pink-500" />;
        case 'relance':
          return <PhoneCall className="w-4 h-4 text-blue-500" />;
        case 'retard':
          return <AlertCircle className="w-4 h-4 text-red-500" />;
        default:
          return <MessageCircle className="w-4 h-4 text-blue-500" />;
      }
    };

    const getBackgroundColor = () => {
      switch (message.type) {
        case 'anniversaire':
          return 'bg-pink-50 border-pink-400';
        case 'relance':
          return 'bg-blue-50 border-blue-400';
        case 'retard':
          return 'bg-red-50 border-red-400';
        default:
          return 'bg-blue-50 border-blue-400';
      }
    };

    return (
      <div className={`p-4 rounded-lg border-l-4 ${getBackgroundColor()}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getIcon()}
            <span className="font-medium text-gray-900">{message.titre}</span>
          </div>
          <span className="text-xs text-gray-500">{message.time}</span>
        </div>
        <p className="mt-1 text-sm text-gray-700">
          <button 
            onClick={() => viewPatientDetails(message.patient_id)}
            className="font-medium text-primary-600 hover:text-primary-800 underline cursor-pointer"
          >
            {message.patient}
          </button>
          {" - " + message.message.replace(message.patient + " - ", "")}
        </p>
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div>
          <h1 className="responsive-title font-bold text-gray-900">
            Bonjour {user.name} 👋
          </h1>
          <p className="text-primary-100 responsive-text">
            Voici un aperçu de votre journée
          </p>
        </div>
      </div>

      {/* Stats Grid - Responsive */}
      <div className="responsive-grid-stats mb-4 sm:mb-6">
        <StatCard
          icon={Calendar}
          title="RDV Aujourd'hui"
          value={stats.total_rdv}
          color="text-blue-600"
          subtitle="Total des rendez-vous"
        />
        <StatCard
          icon={Clock}
          title="Salle attente"
          value={stats.rdv_attente}
          color="text-yellow-600"
          subtitle="Patients en salle d'attente"
        />
        <StatCard
          icon={Users}
          title="Patients Restants"
          value={stats.rdv_restants}
          color="text-orange-600"
          subtitle="Non encore arrivés"
        />
        <StatCard
          icon={Clock}
          title="Temps d'attente"
          value={`${stats.duree_attente_moyenne} min`}
          color="text-teal-600"
          subtitle="Temps d'attente moyen"
        />
        <StatCard
          icon={DollarSign}
          title="Recette du jour"
          value={`${stats.recette_jour} TND`}
          color="text-purple-600"
          subtitle="Paiements encaissés"
        />
      </div>

      {/* Messages and Quick Actions - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* Rappels et alertes */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Rappels et alertes</h3>
            <span className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">
              {messages.filter(m => m.urgent).length} urgent
            </span>
          </div>
          <div className="space-y-2 sm:space-y-3">
            {messages.map((message) => (
              <MessageCard key={message.id} message={message} />
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Actions Rapides</h3>
          <div className="space-y-2 sm:space-y-3">
            <button 
              onClick={handleAddPatient}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Users className="w-4 h-4 sm:w-5 sm:h-5 text-primary-600" />
                <span className="font-medium text-primary-900 responsive-text">Ajouter un patient</span>
              </div>
              <div className="text-primary-600">→</div>
            </button>
            
            <button 
              onClick={handleNewAppointment}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-secondary-600" />
                <span className="font-medium text-secondary-900 responsive-text">Nouveau RDV</span>
              </div>
              <div className="text-secondary-600">→</div>
            </button>
            
            <button 
              onClick={handlePhoneReminders}
              className="w-full flex items-center justify-between p-2 sm:p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 sm:space-x-3">
                <Phone className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
                <span className="font-medium text-green-900 responsive-text">Rappels téléphoniques</span>
              </div>
              <div className="text-green-600">→</div>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity - Responsive */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 responsive-padding">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Activité Récente</h3>
        <div className="space-y-2 sm:space-y-3">
          <div className="flex items-center space-x-2 sm:space-x-3 p-2 sm:p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs sm:text-sm text-gray-700">Consultation terminée - Omar Tazi (14:30)</span>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-3 p-2 sm:p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-xs sm:text-sm text-gray-700">Paiement encaissé - 300 TND (14:35)</span>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-3 p-2 sm:p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <span className="text-xs sm:text-sm text-gray-700">Patient en attente - Yassine Ben Ahmed (Salle 1)</span>
          </div>
        </div>
      </div>

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

export default Dashboard;