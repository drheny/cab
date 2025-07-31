import React, { useState, useEffect, useMemo } from 'react';
import { 
  DollarSign, 
  Download, 
  TrendingUp,
  Users,
  RefreshCw,
  X,
  Calendar,
  BarChart3,
  LineChart,
  Target,
  Award,
  Search,
  FileText,
  CreditCard,
  Edit,
  Trash2,
  Eye,
  PieChart
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import PaymentModal from './PaymentModal';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const Billing = ({ user }) => {
  // API Base URL
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // States for data
  const [enhancedStats, setEnhancedStats] = useState({});
  const [topPatients, setTopPatients] = useState([]);
  const [evolutionData, setEvolutionData] = useState([]);
  const [predictiveAnalysis, setPredictiveAnalysis] = useState(null);
  
  // States for UI
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // New states for enhanced features
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [dailyPayments, setDailyPayments] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState(null);
  const [yearlyStats, setYearlyStats] = useState(null);
  
  // States for payments tab
  const [payments, setPayments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [searchFilters, setSearchFilters] = useState({
    patientName: '',
    dateDebut: '',
    dateFin: '',
    statutPaiement: '',
    assure: '',
    typeConsultation: ''
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  
  // Real-time search states
  const [patientSuggestions, setPatientSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Charts data states
  const [chartsData, setChartsData] = useState(null);
  const [chartsLoading, setChartsLoading] = useState(false);
  
  // Modal states for patient and consultation
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [selectedPatientData, setSelectedPatientData] = useState(null);
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  const [selectedConsultationData, setSelectedConsultationData] = useState(null);
  
  // States for cash management (caisse)
  const [cashMovements, setCashMovements] = useState([]);
  const [showCashForm, setShowCashForm] = useState(false);
  const [cashForm, setCashForm] = useState({
    montant: '',
    type_mouvement: 'ajout',
    date: new Date().toISOString().split('T')[0],
    motif: ''
  });
  
  // Export states
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportOptions, setExportOptions] = useState({
    date: true,
    patient: true,
    montant: true,
    assurance: true,
    indicateurs: {
      ca: true,
      visites: true
    }
  });
  
  // New states for predictions section
  const [predictions, setPredictions] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);

  // Add real-time patient search effect
  useEffect(() => {
    if (searchFilters.patientName && searchFilters.patientName.length >= 2) {
      // Real-time patient search with debounce
      const timer = setTimeout(() => {
        const filtered = patients.filter(patient => {
          const fullName = `${patient.prenom || ''} ${patient.nom || ''}`.toLowerCase();
          return fullName.includes(searchFilters.patientName.toLowerCase());
        });
        setPatientSuggestions(filtered.slice(0, 5)); // Limit to 5 suggestions
        setShowSuggestions(filtered.length > 0);
      }, 300); // 300ms debounce

      return () => clearTimeout(timer);
    } else {
      setPatientSuggestions([]);
      setShowSuggestions(false);
    }
  }, [searchFilters.patientName, patients]);

  useEffect(() => {
    fetchInitialData();
    fetchPatients();  // Added this back
    fetchChartsData();  // Added for statistics tab
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchEnhancedStats(),
        fetchEvolutionData(),
        fetchPredictiveAnalysis(),
        fetchPayments(),
        fetchCashMovements()
      ]);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const fetchEnhancedStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/enhanced-stats`);
      setEnhancedStats(response.data || {});
    } catch (error) {
      console.error('Error fetching enhanced stats:', error);
    }
  };

  const fetchEvolutionData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/evolution-graphs`, {
        params: { period: 'month', year: new Date().getFullYear() }
      });
      setEvolutionData(response.data?.evolution || []);
    } catch (error) {
      console.error('Error fetching evolution data:', error);
    }
  };

  const fetchPredictiveAnalysis = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/predictions`);
      setPredictiveAnalysis(response.data);
    } catch (error) {
      console.error('Error fetching predictive analysis:', error);
    }
  };

  // New functions for predictions section
  const fetchPredictions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/advanced-reports`);
      setPredictions(response.data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
      toast.error('Erreur lors du chargement des prédictions');
    }
  };

  const fetchAnalysisData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/ai-medical-report`);
      setAnalysisData(response.data);
    } catch (error) {
      console.error('Error fetching analysis data:', error);
      toast.error('Erreur lors du chargement des analyses');
    }
  };

  const fetchTopPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/top-patients?limit=10`);
      return response.data?.top_patients || [];
    } catch (error) {
      console.error('Error fetching top patients:', error);
      return [];
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments`);
      // API returns array directly, not wrapped in payments property
      setPayments(Array.isArray(response.data) ? response.data : response.data?.payments || []);
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(response.data?.patients || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const fetchChartsData = async () => {
    try {
      setChartsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/admin/charts/yearly-evolution`);
      setChartsData(response.data);
    } catch (error) {
      console.error('Error fetching charts data:', error);
      toast.error('Erreur lors du chargement des graphiques');
    } finally {
      setChartsLoading(false);
    }
  };

  const fetchCashMovements = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/cash-movements`);
      setCashMovements(response.data?.movements || []);
    } catch (error) {
      console.error('Error fetching cash movements:', error);
    }
  };

  const fetchDailyPayments = async (date) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/daily-payments`, {
        params: { date }
      });
      setDailyPayments(response.data);
    } catch (error) {
      console.error('Error fetching daily payments:', error);
      toast.error('Erreur lors du chargement des paiements du jour');
    }
  };

  const fetchMonthlyStats = async (year, month) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/monthly-stats-with-evolution`, {
        params: { year, month }
      });
      setMonthlyStats(response.data);
    } catch (error) {
      console.error('Error fetching monthly stats:', error);
      toast.error('Erreur lors du chargement des statistiques mensuelles');
    }
  };

  const fetchYearlyStats = async (year) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/yearly-stats`, {
        params: { year }
      });
      setYearlyStats(response.data);
    } catch (error) {
      console.error('Error fetching yearly stats:', error);
      toast.error('Erreur lors du chargement des statistiques annuelles');
    }
  };

  // Advanced search functions
  const handleAdvancedSearch = async () => {
    setIsSearching(true);
    try {
      // Use the filteredPayments directly instead of making API call
      // This avoids potential API errors and provides real-time filtering
      setSearchResults(filteredPayments);
      toast.success(`${filteredPayments.length} paiement(s) trouvé(s)`);
    } catch (error) {
      console.error('Error searching payments:', error);
      toast.error('Erreur lors de la recherche');
    } finally {
      setIsSearching(false);
    }
  };

  const clearAdvancedSearch = () => {
    setSearchFilters({
      patientName: '',
      dateDebut: '',
      dateFin: '',
      statutPaiement: '',
      assure: '',
      typeConsultation: ''
    });
    setSearchResults([]);
  };

  const handleViewPayment = (payment) => {
    setSelectedPayment(payment);
    setShowPaymentModal(true);
  };

  const handleEditPayment = (payment) => {
    // Transform payment data to match appointment structure expected by PaymentModal
    const appointmentData = {
      id: payment.appointment_id,
      patient: payment.patient,
      date: payment.date,
      heure: payment.heure || '09:00', // Default time if not available
      type_rdv: payment.type_rdv,
      paye: payment.statut === 'paye',
      montant_paye: payment.montant,
      assure: payment.assure
    };
    
    setEditingPayment(appointmentData);
    setShowEditModal(true);
  };

  const handleViewPatient = async (patient) => {
    try {
      // Use the patient data already available in the payment object
      if (patient) {
        // Find the patient in our patients list using name matching if ID not available
        let patientData = null;
        
        if (patient.id) {
          // If we have an ID, use it
          const response = await axios.get(`${API_BASE_URL}/api/patients`);
          patientData = response.data.patients.find(p => p.id === patient.id);
        } else if (patient.prenom && patient.nom) {
          // If no ID, match by name
          const response = await axios.get(`${API_BASE_URL}/api/patients`);
          patientData = response.data.patients.find(p => 
            p.prenom.toLowerCase() === patient.prenom.toLowerCase() && 
            p.nom.toLowerCase() === patient.nom.toLowerCase()
          );
        }
        
        if (patientData) {
          setSelectedPatientData(patientData);
          setShowPatientModal(true);
        } else {
          toast.error('Patient non trouvé dans la base de données');
        }
      } else {
        toast.error('Données patient non disponibles');
      }
    } catch (error) {
      console.error('Error fetching patient data:', error);
      toast.error('Erreur lors du chargement des données du patient');
    }
  };

  const handleViewConsultation = async (payment) => {
    try {
      // Get consultation data based on appointment_id
      const response = await axios.get(`${API_BASE_URL}/api/consultations`);
      const consultationData = response.data.find(c => c.appointment_id === payment.appointment_id);
      
      if (consultationData) {
        // Add patient info to consultation data
        consultationData.patient = payment.patient;
        setSelectedConsultationData(consultationData);
        setShowConsultationModal(true);
      } else {
        toast.error('Consultation non trouvée');
      }
    } catch (error) {
      console.error('Error fetching consultation data:', error);
      toast.error('Erreur lors du chargement des données de consultation');
    }
  };

  const handleDeletePayment = async (payment) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce paiement ?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/payments/${payment.id}`);
        toast.success('Paiement supprimé avec succès');
        fetchPayments(); // Reload payments list
      } catch (error) {
        console.error('Error deleting payment:', error);
        toast.error('Erreur lors de la suppression du paiement');
      }
    }
  };

  // Cash management functions
  const handleCreateCashMovement = async () => {
    if (!cashForm.montant || !cashForm.motif) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/api/cash-movements`, {
        ...cashForm,
        montant: parseFloat(cashForm.montant)
      });
      
      toast.success('Mouvement de caisse enregistré');
      setCashForm({
        montant: '',
        type_mouvement: 'ajout',
        date: new Date().toISOString().split('T')[0],
        motif: ''
      });
      setShowCashForm(false);
      fetchCashMovements();
    } catch (error) {
      console.error('Error creating cash movement:', error);
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const handleDeleteCashMovement = async (movementId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce mouvement ?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/cash-movements/${movementId}`);
        toast.success('Mouvement supprimé avec succès');
        fetchCashMovements();
      } catch (error) {
        console.error('Error deleting cash movement:', error);
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-TN', {
      style: 'currency',
      currency: 'TND',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const exportToExcel = () => {
    setShowExportModal(true);
  };

  const handleCustomExport = () => {
    try {
      // Prepare headers based on selected options
      const headers = [];
      if (exportOptions.date) headers.push('Date');
      if (exportOptions.patient) headers.push('Patient');
      if (exportOptions.montant) headers.push('Montant (TND)');
      if (exportOptions.assurance) headers.push('Assuré');
      
      // Create simple CSV data
      const csvData = [
        ['=== STATISTIQUES ENHANCÉES ==='],
        ['Recette du jour:', `${formatCurrency(enhancedStats.recette_jour || 0)}`],
        ['Recette du mois:', `${formatCurrency(enhancedStats.recette_mois || 0)}`],
        ['Recette de l\'année:', `${formatCurrency(enhancedStats.recette_annee || 0)}`],
        ['Nouveaux patients cette année:', enhancedStats.nouveaux_patients_annee || 0],
        []
      ];
      
      // Add evolution data section if available
      if (evolutionData.length > 0) {
        csvData.push(['=== ÉVOLUTION MENSUELLE ===']);
        csvData.push(['Mois', 'Recette (TND)', 'Nb Consultations', 'Nouveaux Patients']);
        evolutionData.forEach(data => {
          csvData.push([
            data.mois,
            data.recette,
            data.nb_consultations,
            data.nouveaux_patients || 0
          ]);
        });
      }

      // Create CSV content
      const csvContent = csvData
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');

      // Download file with enhanced filename
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      const today = new Date().toISOString().split('T')[0];
      const filename = `facturation_enhanced_${today}.csv`;
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success('Export CSV avancé téléchargé avec succès');
      setShowExportModal(false);
      
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Erreur lors de l\'export');
    }
  };

  // Utility functions
  const filteredPayments = useMemo(() => {
    return payments.filter(payment => {
      const matchesName = !searchFilters.patientName || 
        `${payment.patient?.prenom} ${payment.patient?.nom}`.toLowerCase()
        .includes(searchFilters.patientName.toLowerCase());
      
      const matchesStatus = !searchFilters.statutPaiement || 
        payment.statut === searchFilters.statutPaiement;
      
      const matchesAssurance = searchFilters.assure === '' || 
        payment.assure.toString() === searchFilters.assure;

      const matchesType = !searchFilters.typeConsultation || 
        payment.type_rdv === searchFilters.typeConsultation;

      // Date filtering
      const paymentDate = new Date(payment.date);
      const matchesStartDate = !searchFilters.dateDebut || 
        paymentDate >= new Date(searchFilters.dateDebut);
      const matchesEndDate = !searchFilters.dateFin || 
        paymentDate <= new Date(searchFilters.dateFin);
      
      return matchesName && matchesStatus && matchesAssurance && matchesType && matchesStartDate && matchesEndDate;
    });
  }, [payments, searchFilters]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facturation & Paiements</h1>
          <p className="text-gray-600">Gestion financière du cabinet</p>
        </div>
        {/* Refresh buttons fix - make sure they are properly connected */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setLoading(true);
              fetchInitialData().finally(() => setLoading(false));
            }}
            disabled={loading}
            className="btn-outline flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          <button
            onClick={exportToExcel}
            className="btn-primary flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Exporter</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'dashboard', label: 'Tableau de bord', icon: PieChart },
            { id: 'payments', label: 'Historique paiements', icon: CreditCard },
            { id: 'stats', label: 'Statistiques', icon: BarChart3 },
            { id: 'caisse', label: 'Caisse', icon: DollarSign }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Enhanced Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">Recette du jour</p>
                  <p className="text-2xl font-bold">{formatCurrency(enhancedStats.recette_jour || 0)}</p>
                  <p className="text-green-100 text-xs mt-1">
                    {new Date().toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <div className="bg-green-400 bg-opacity-30 rounded-full p-3">
                  <DollarSign className="w-6 h-6" />
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-medium">Recette du mois</p>
                  <p className="text-2xl font-bold">{formatCurrency(enhancedStats.recette_mois || 0)}</p>
                  <p className="text-blue-100 text-xs mt-1">
                    {new Date().toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })}
                  </p>
                </div>
                <div className="bg-blue-400 bg-opacity-30 rounded-full p-3">
                  <Calendar className="w-6 h-6" />
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-medium">Recette de l'année</p>
                  <p className="text-2xl font-bold">{formatCurrency(enhancedStats.recette_annee || 0)}</p>
                  <p className="text-purple-100 text-xs mt-1">
                    {new Date().getFullYear()}
                  </p>
                </div>
                <div className="bg-purple-400 bg-opacity-30 rounded-full p-3">
                  <TrendingUp className="w-6 h-6" />
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm font-medium">Nouveaux patients</p>
                  <p className="text-2xl font-bold">{enhancedStats.nouveaux_patients_annee || 0}</p>
                  <p className="text-orange-100 text-xs mt-1">
                    Depuis début {new Date().getFullYear()}
                  </p>
                </div>
                <div className="bg-orange-400 bg-opacity-30 rounded-full p-3">
                  <Users className="w-6 h-6" />
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Payment History Section */}
          <div className="space-y-6">
            {/* Optimized Payment History */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">Historique de paiements</h3>
              
              {/* Simplified Search Options */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* Daily Search */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Recherche par jour
                  </h4>
                  <div className="space-y-3">
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="input-field w-full"
                    />
                    <button
                      onClick={() => fetchDailyPayments(selectedDate)}
                      className="btn-primary w-full"
                    >
                      Voir
                    </button>
                  </div>
                </div>
                
                {/* Monthly Search */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Recherche par mois
                  </h4>
                  <div className="space-y-3">
                    <input
                      type="month"
                      onChange={(e) => {
                        const [year, month] = e.target.value.split('-');
                        if (year && month) {
                          setMonthlyStats(null);
                        }
                      }}
                      className="input-field w-full"
                      id="monthlySearch"
                    />
                    <button
                      onClick={() => {
                        const monthInput = document.getElementById('monthlySearch');
                        if (monthInput.value) {
                          const [year, month] = monthInput.value.split('-');
                          fetchMonthlyStats(parseInt(year), parseInt(month));
                        } else {
                          toast.error('Veuillez sélectionner un mois');
                        }
                      }}
                      className="btn-primary w-full"
                    >
                      Voir
                    </button>
                  </div>
                </div>
                
                {/* Yearly Search */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Recherche par année
                  </h4>
                  <div className="space-y-3">
                    <input
                      type="number"
                      min="2020"
                      max="2030"
                      defaultValue={new Date().getFullYear()}
                      onChange={(e) => {
                        if (e.target.value) {
                          setYearlyStats(null);
                        }
                      }}
                      className="input-field w-full"
                      id="yearlySearch"
                    />
                    <button
                      onClick={() => {
                        const yearInput = document.getElementById('yearlySearch');
                        if (yearInput.value) {
                          fetchYearlyStats(parseInt(yearInput.value));
                        } else {
                          toast.error('Veuillez sélectionner une année');
                        }
                      }}
                      className="btn-primary w-full"
                    >
                      Voir
                    </button>
                  </div>
                </div>
              </div>

              {/* Results Display Sections */}
              {dailyPayments && (
                <div className="mt-6 bg-green-50 rounded-lg p-4 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-3">
                    Résultats pour le {new Date(dailyPayments.date).toLocaleDateString('fr-FR')}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-700">{dailyPayments.totals.recette_totale} DT</div>
                      <div className="text-sm text-green-600">Recette totale</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-700">{dailyPayments.totals.nb_total}</div>
                      <div className="text-sm text-green-600">Total paiements</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-700">{dailyPayments.totals.nb_visites}</div>
                      <div className="text-sm text-green-600">Visites</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-700">{dailyPayments.totals.nb_assures}</div>
                      <div className="text-sm text-green-600">Assurés</div>
                    </div>
                  </div>
                  {dailyPayments.payments.length > 0 ? (
                    <div className="space-y-2">
                      <div className="text-sm font-semibold text-green-900">Détail des paiements :</div>
                      {dailyPayments.payments.slice(0, 5).map((payment, index) => (
                        <div key={index} className="flex justify-between items-center bg-white p-2 rounded border">
                          <span className="text-sm">{payment.patient?.prenom} {payment.patient?.nom}</span>
                          <span className="font-semibold text-green-700">{payment.montant} DT</span>
                        </div>
                      ))}
                      {dailyPayments.payments.length > 5 && (
                        <div className="text-xs text-green-600 text-center">
                          ... et {dailyPayments.payments.length - 5} autre(s) paiement(s)
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-green-600">Aucun paiement pour cette date</div>
                  )}
                </div>
              )}

              {monthlyStats && (
                <div className="mt-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">
                    Résultats pour {monthlyStats.month}/{monthlyStats.year}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">{monthlyStats.recette_mois} DT</div>
                      <div className="text-sm text-blue-600">Recette mensuelle</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">{monthlyStats.nb_total_rdv}</div>
                      <div className="text-sm text-blue-600">Total RDV</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">{monthlyStats.nb_visites}</div>
                      <div className="text-sm text-blue-600">Visites</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-700">{monthlyStats.nb_assures}</div>
                      <div className="text-sm text-blue-600">Assurés</div>
                    </div>
                  </div>
                  {monthlyStats.evolution && (
                    <div className="bg-white p-3 rounded border">
                      <div className="text-sm font-semibold text-blue-900 mb-2">Évolution par rapport au mois précédent :</div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Recette précédente: {monthlyStats.evolution.recette_precedente} DT</span>
                        <span className={`font-semibold ${monthlyStats.evolution.evolution_pourcentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {monthlyStats.evolution.evolution_pourcentage >= 0 ? '+' : ''}{monthlyStats.evolution.evolution_pourcentage}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {yearlyStats && (
                <div className="mt-6 bg-purple-50 rounded-lg p-4 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-3">
                    Résultats pour l'année {yearlyStats.year}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-700">{yearlyStats.recette_annee} DT</div>
                      <div className="text-sm text-purple-600">Recette annuelle</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-700">{yearlyStats.nb_total_rdv}</div>
                      <div className="text-sm text-purple-600">Total RDV</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-700">{yearlyStats.nb_visites}</div>
                      <div className="text-sm text-purple-600">Visites</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-700">{yearlyStats.nb_assures}</div>
                      <div className="text-sm text-purple-600">Assurés</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Payments Tab */}
      {activeTab === 'payments' && (
        <div className="space-y-6">
          {/* Advanced Search Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recherche avancée</h3>
            
            {/* Advanced Search */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 Recherche Avancée</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Patient Search */}
                <div className="relative col-span-1 md:col-span-2 lg:col-span-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recherche Patient
                  </label>
                  <input
                    type="text"
                    placeholder="Tapez le nom du patient..."
                    value={searchFilters.patientName}
                    onChange={(e) => {
                      setSearchFilters(prev => ({ ...prev, patientName: e.target.value }));
                    }}
                    onFocus={() => {
                      if (patientSuggestions.length > 0) {
                        setShowSuggestions(true);
                      }
                    }}
                    onBlur={() => {
                      // Delay hiding to allow clicking on suggestions
                      setTimeout(() => setShowSuggestions(false), 150);
                    }}
                    className="input-field w-full"
                  />
                  {/* Patient Suggestions Dropdown */}
                  {showSuggestions && patientSuggestions.length > 0 && (
                    <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                      {patientSuggestions.map((patient) => (
                        <div
                          key={patient.id}
                          className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                          onMouseDown={() => {
                            const fullName = `${patient.prenom} ${patient.nom}`;
                            setSearchFilters(prev => ({ ...prev, patientName: fullName }));
                            setShowSuggestions(false);
                          }}
                        >
                          <div className="font-medium">{patient.prenom} {patient.nom}</div>
                          {patient.numero_whatsapp && (
                            <div className="text-xs text-gray-500">{patient.numero_whatsapp}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Date Range */}
                <div className="grid grid-cols-2 gap-2 col-span-1 md:col-span-2 lg:col-span-1">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date début</label>
                    <input
                      type="date"
                      value={searchFilters.dateDebut}
                      onChange={(e) => setSearchFilters(prev => ({ ...prev, dateDebut: e.target.value }))}
                      className="input-field w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date fin</label>
                    <input
                      type="date"
                      value={searchFilters.dateFin}
                      onChange={(e) => setSearchFilters(prev => ({ ...prev, dateFin: e.target.value }))}
                      className="input-field w-full"
                    />
                  </div>
                </div>

                {/* Filters Row */}
                <div className="grid grid-cols-3 gap-2 col-span-1 md:col-span-2 lg:col-span-1">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select
                      value={searchFilters.typeConsultation}
                      onChange={(e) => setSearchFilters(prev => ({ ...prev, typeConsultation: e.target.value }))}
                      className="input-field text-xs"
                    >
                      <option value="">Tous</option>
                      <option value="visite">Visite</option>
                      <option value="controle">Contrôle</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Statut</label>
                    <select
                      value={searchFilters.statutPaiement}
                      onChange={(e) => setSearchFilters(prev => ({ ...prev, statutPaiement: e.target.value }))}
                      className="input-field text-xs"
                    >
                      <option value="">Tous</option>
                      <option value="paye">Payé</option>
                      <option value="impaye">Impayé</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Assurance</label>
                    <select
                      value={searchFilters.assure}
                      onChange={(e) => setSearchFilters(prev => ({ ...prev, assure: e.target.value }))}
                      className="input-field text-xs"
                    >
                      <option value="">Tous</option>
                      <option value="true">Assuré</option>
                      <option value="false">Non assuré</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {filteredPayments.length} paiement{filteredPayments.length !== 1 ? 's' : ''} trouvé{filteredPayments.length !== 1 ? 's' : ''}
                {/* Debug info */}
                <span className="text-xs text-gray-400 ml-2">
                  (Total DB: {payments.length})
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    // Clear all filters to show all payments
                    setSearchFilters({
                      patientName: '',
                      dateDebut: '',
                      dateFin: '',
                      statutPaiement: '',
                      assure: '',
                      typeConsultation: ''
                    });
                    setSearchResults([]);
                  }}
                  className="btn-outline text-sm bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
                >
                  Tout Afficher
                </button>
                <button
                  onClick={clearAdvancedSearch}
                  className="btn-outline text-sm"
                >
                  Réinitialiser
                </button>
                <button
                  onClick={handleAdvancedSearch}
                  className="btn-primary text-sm flex items-center space-x-2"
                >
                  <Search className="w-4 h-4" />
                  <span>Rechercher</span>
                </button>
              </div>
            </div>
          </div>

          {/* Payments List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Historique des paiements</h3>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <RefreshCw className="w-6 h-6 animate-spin text-primary-500" />
                <span className="ml-2">Chargement...</span>
              </div>
            ) : filteredPayments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Patient
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Montant
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statut Paiement
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Assurance
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredPayments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleViewPatient(payment.patient)}
                            className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                          >
                            {payment.patient?.prenom} {payment.patient?.nom}
                          </button>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {new Date(payment.date).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            payment.statut === 'paye' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {payment.type_rdv === 'controle' ? '0 TND' : `${payment.montant} TND`}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            payment.type_rdv === 'visite'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-purple-100 text-purple-800'
                          }`}>
                            {payment.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            payment.statut === 'paye' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {payment.statut === 'paye' ? 'Payé' : 'Impayé'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            payment.assure 
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {payment.assure ? 'Assuré' : 'Non assuré'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={() => handleViewConsultation(payment)}
                              className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                              title="Voir la consultation"
                            >
                              👁️
                            </button>
                            <button
                              onClick={() => handleEditPayment(payment)}
                              className="p-1 text-yellow-600 hover:bg-yellow-100 rounded"
                              title="Éditer le paiement"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeletePayment(payment)}
                              className="p-1 text-red-600 hover:bg-red-100 rounded"
                              title="Supprimer le paiement"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Patient
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Montant
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statut Paiement
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Assurance
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                        Aucun paiement trouvé pour les critères sélectionnés
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stats Tab Content */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <TrendingUp className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Évolution Annuelle {chartsData?.year || new Date().getFullYear()}</h2>
              <button
                onClick={fetchChartsData}
                disabled={chartsLoading}
                className="ml-auto flex items-center space-x-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${chartsLoading ? 'animate-spin' : ''}`} />
                <span>Actualiser</span>
              </button>
            </div>

            {chartsLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              </div>
            ) : chartsData ? (
              <div className="space-y-8">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <DollarSign className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">Recette Annuelle</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600">{chartsData.totals?.recette_annee || 0} TND</p>
                  </div>
                  
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Users className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-900">Nouveaux Patients</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600">{chartsData.totals?.nouveaux_patients_annee || 0}</p>
                  </div>
                  
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <BarChart3 className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-purple-900">Consultations</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-600">{chartsData.totals?.consultations_annee || 0}</p>
                  </div>
                </div>

                {/* Charts Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Revenue Evolution Chart */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Évolution de la Recette</h3>
                    <div className="h-64">
                      <Line
                        data={{
                          labels: chartsData.monthly_data?.map(d => d.month_short) || [],
                          datasets: [
                            {
                              label: 'Recette (TND)',
                              data: chartsData.monthly_data?.map(d => d.recette_mensuelle) || [],
                              borderColor: 'rgb(59, 130, 246)',
                              backgroundColor: 'rgba(59, 130, 246, 0.1)',
                              tension: 0.1,
                              fill: true
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: false
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              ticks: {
                                callback: function(value) {
                                  return value + ' TND';
                                }
                              }
                            }
                          }
                        }}
                      />
                    </div>
                  </div>

                  {/* New Patients Chart */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Nouveaux Patients par Mois</h3>
                    <div className="h-64">
                      <Bar
                        data={{
                          labels: chartsData.monthly_data?.map(d => d.month_short) || [],
                          datasets: [
                            {
                              label: 'Nouveaux Patients',
                              data: chartsData.monthly_data?.map(d => d.nouveaux_patients) || [],
                              backgroundColor: 'rgba(34, 197, 94, 0.8)',
                              borderColor: 'rgb(34, 197, 94)',
                              borderWidth: 1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: false
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              ticks: {
                                stepSize: 1
                              }
                            }
                          }
                        }}
                      />
                    </div>
                  </div>

                  {/* Consultations Evolution Chart */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Évolution des Consultations</h3>
                    <div className="h-64">
                      <Line
                        data={{
                          labels: chartsData.monthly_data?.map(d => d.month_short) || [],
                          datasets: [
                            {
                              label: 'Visites',
                              data: chartsData.monthly_data?.map(d => d.nb_visites) || [],
                              borderColor: 'rgb(147, 51, 234)',
                              backgroundColor: 'rgba(147, 51, 234, 0.1)',
                              tension: 0.1
                            },
                            {
                              label: 'Contrôles',
                              data: chartsData.monthly_data?.map(d => d.nb_controles) || [],
                              borderColor: 'rgb(245, 158, 11)',
                              backgroundColor: 'rgba(245, 158, 11, 0.1)',
                              tension: 0.1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top'
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              ticks: {
                                stepSize: 1
                              }
                            }
                          }
                        }}
                      />
                    </div>
                  </div>

                  {/* Total Consultations Chart */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Total Consultations par Mois</h3>
                    <div className="h-64">
                      <Bar
                        data={{
                          labels: chartsData.monthly_data?.map(d => d.month_short) || [],
                          datasets: [
                            {
                              label: 'Total Consultations',
                              data: chartsData.monthly_data?.map(d => d.consultations_totales) || [],
                              backgroundColor: 'rgba(168, 85, 247, 0.8)',
                              borderColor: 'rgb(168, 85, 247)',
                              borderWidth: 1
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: false
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              ticks: {
                                stepSize: 1
                              }
                            }
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Aucune donnée statistique disponible</p>
                <button
                  onClick={fetchChartsData}
                  className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Charger les statistiques
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Caisse Tab */}
      {activeTab === 'caisse' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Gestion de la caisse</h3>
                <p className="text-sm text-gray-600">
                  Ajustements de la recette du jour pour les dépenses ou encaissements
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setShowCashForm(true)}
                  className="btn-primary flex items-center space-x-2"
                >
                  <DollarSign className="w-4 h-4" />
                  <span>Nouveau mouvement</span>
                </button>
              </div>
            </div>
          </div>

          {/* Cash Movement Form */}
          {showCashForm && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900">Nouveau mouvement de caisse</h4>
                <button
                  onClick={() => setShowCashForm(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Montant (TND) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={cashForm.montant}
                    onChange={(e) => setCashForm(prev => ({ ...prev, montant: e.target.value }))}
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type *
                  </label>
                  <select
                    value={cashForm.type_mouvement}
                    onChange={(e) => setCashForm(prev => ({ ...prev, type_mouvement: e.target.value }))}
                    className="input-field"
                  >
                    <option value="ajout">Ajout (+)</option>
                    <option value="soustraction">Soustraction (-)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date *
                  </label>
                  <input
                    type="date"
                    value={cashForm.date}
                    onChange={(e) => setCashForm(prev => ({ ...prev, date: e.target.value }))}
                    className="input-field"
                  />
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={handleCreateCashMovement}
                    className="btn-primary w-full"
                  >
                    Enregistrer
                  </button>
                </div>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Motif *
                </label>
                <input
                  type="text"
                  placeholder="Ex: Achat fournitures, Paiement en retard encaissé..."
                  value={cashForm.motif}
                  onChange={(e) => setCashForm(prev => ({ ...prev, motif: e.target.value }))}
                  className="input-field"
                />
              </div>
            </div>
          )}

          {/* Cash Movements History */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Historique des mouvements</h3>
              <p className="text-sm text-gray-600 mt-1">
                {cashMovements.length} mouvement(s) enregistré(s)
              </p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Montant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Motif
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {cashMovements.map((movement) => (
                    <tr key={movement.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(movement.date).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {movement.type_mouvement === 'ajout' ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            Ajout
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <TrendingUp className="w-3 h-3 mr-1 rotate-180" />
                            Soustraction
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${
                          movement.type_mouvement === 'ajout' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {movement.type_mouvement === 'ajout' ? '+' : '-'}{formatCurrency(movement.montant)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {movement.motif}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleDeleteCashMovement(movement.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Supprimer le mouvement"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Empty State for Cash Movements */}
          {cashMovements.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun mouvement de caisse enregistré</p>
              <button
                onClick={() => setShowCashForm(true)}
                className="mt-4 btn-primary"
              >
                Ajouter le premier mouvement
              </button>
            </div>
          )}
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Export personnalisé</h3>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h4 className="text-md font-semibold text-gray-900 mb-3">Champs à inclure</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.date}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          date: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Date</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.patient}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          patient: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Patient</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.montant}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          montant: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Montant</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.assurance}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          assurance: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Assurance</span>
                    </label>
                  </div>
                </div>

                <div>
                  <h4 className="text-md font-semibold text-gray-900 mb-3">Indicateurs statistiques</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs?.ca}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, ca: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Chiffre d'affaires</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs?.visites}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, visites: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Nombre de visites</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="btn-outline"
                >
                  Annuler
                </button>
                <button
                  onClick={handleCustomExport}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Exporter CSV</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Details Modal */}
      {showPaymentModal && selectedPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Détails du paiement</h3>
                <button
                  onClick={() => setShowPaymentModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Patient</label>
                  <p className="text-sm text-gray-900">
                    {selectedPayment.patient?.prenom} {selectedPayment.patient?.nom}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Date</label>
                  <p className="text-sm text-gray-900">
                    {new Date(selectedPayment.date).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Montant</label>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(selectedPayment.montant)}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Assurance</label>
                  <p className="text-sm text-gray-900">
                    {selectedPayment.assure ? 'Assuré' : 'Non assuré'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowPaymentModal(false)}
                  className="btn-outline"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Patient Modal */}
      {showPatientModal && selectedPatientData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                👤 Fiche Complète du Patient
              </h2>
              <button
                onClick={() => setShowPatientModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Informations personnelles */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Informations Personnelles</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Prénom</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">{selectedPatientData.prenom}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nom</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">{selectedPatientData.nom}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Sexe</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.sexe || 'Non renseigné'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date de naissance</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedPatientData.date_naissance ? new Date(selectedPatientData.date_naissance).toLocaleDateString('fr-FR') : 'Non renseignée'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Âge</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.age || 'Non calculé'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Téléphone</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.telephone || 'Non renseigné'}</p>
                  </div>
                </div>
                
                {selectedPatientData.adresse && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">Adresse</label>
                    <p className="mt-1 text-sm text-gray-900 bg-white p-2 rounded">{selectedPatientData.adresse}</p>
                  </div>
                )}
              </div>

              {/* Contact et Communication */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-900 mb-4">Contact & Communication</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">WhatsApp</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.numero_whatsapp || 'Non renseigné'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nom parent/tuteur</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.nom_parent || 'Non renseigné'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Téléphone parent</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedPatientData.telephone_parent || 'Non renseigné'}</p>
                  </div>
                </div>
              </div>

              {/* Parents (si disponibles) */}
              {(selectedPatientData.pere || selectedPatientData.mere) && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-yellow-900 mb-4">Informations Parents</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedPatientData.pere && (
                      <div className="bg-white p-3 rounded">
                        <h4 className="font-medium text-gray-800 mb-2">👨 Père</h4>
                        <p><strong>Nom:</strong> {selectedPatientData.pere.nom}</p>
                        <p><strong>Téléphone:</strong> {selectedPatientData.pere.telephone}</p>
                        <p><strong>Fonction:</strong> {selectedPatientData.pere.fonction}</p>
                      </div>
                    )}
                    {selectedPatientData.mere && (
                      <div className="bg-white p-3 rounded">
                        <h4 className="font-medium text-gray-800 mb-2">👩 Mère</h4>
                        <p><strong>Nom:</strong> {selectedPatientData.mere.nom}</p>
                        <p><strong>Téléphone:</strong> {selectedPatientData.mere.telephone}</p>
                        <p><strong>Fonction:</strong> {selectedPatientData.mere.fonction}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Notes et Antécédents */}
              {(selectedPatientData.notes || selectedPatientData.antecedents) && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Notes & Antécédents</h3>
                  {selectedPatientData.notes && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                      <p className="text-sm text-gray-900 bg-white p-3 rounded-lg">{selectedPatientData.notes}</p>
                    </div>
                  )}
                  {selectedPatientData.antecedents && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Antécédents</label>
                      <p className="text-sm text-gray-900 bg-white p-3 rounded-lg">{selectedPatientData.antecedents}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Historique des consultations */}
              {selectedPatientData.consultations && selectedPatientData.consultations.length > 0 && (
                <div className="bg-indigo-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-indigo-900 mb-4">Historique des Consultations</h3>
                  <div className="space-y-2">
                    {selectedPatientData.consultations.map((consultation, index) => (
                      <div key={index} className="bg-white p-3 rounded-lg flex justify-between items-center">
                        <div>
                          <span className="font-medium">{consultation.date}</span>
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                            consultation.type === 'visite' 
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-purple-100 text-purple-800'
                          }`}>
                            {consultation.type}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">ID: {consultation.id_consultation}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Première consultation</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedPatientData.date_premiere_consultation || 'Non renseignée'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Dernière consultation</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedPatientData.date_derniere_consultation || 'Non renseignée'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowPatientModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Consultation Modal */}
      {showConsultationModal && selectedConsultationData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                🩺 Détails de la Consultation
              </h2>
              <button
                onClick={() => setShowConsultationModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Informations générales */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Informations Générales</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Patient</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">
                      {selectedConsultationData.patient?.prenom} {selectedConsultationData.patient?.nom}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedConsultationData.date ? new Date(selectedConsultationData.date).toLocaleDateString('fr-FR') : 'Non renseignée'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Durée</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedConsultationData.duree || 'Non renseignée'} min</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Type</label>
                    <p className="mt-1 text-sm">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        selectedConsultationData.type_rdv === 'visite'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {selectedConsultationData.type_rdv === 'visite' ? 'Visite' : 'Contrôle'}
                      </span>
                    </p>
                  </div>
                </div>
              </div>

              {/* Mesures physiques */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-900 mb-4">Mesures Physiques</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Poids</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">{selectedConsultationData.poids || 'Non renseigné'} kg</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Taille</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">{selectedConsultationData.taille || 'Non renseignée'} cm</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Périmètre Crânien</label>
                    <p className="mt-1 text-sm text-gray-900 font-medium">{selectedConsultationData.pc || 'Non renseigné'} cm</p>
                  </div>
                </div>
              </div>

              {/* Observations cliniques */}
              {selectedConsultationData.observations && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-yellow-900 mb-4">Observations Cliniques</h3>
                  <p className="text-sm text-gray-900 bg-white p-4 rounded-lg leading-relaxed">
                    {selectedConsultationData.observations}
                  </p>
                </div>
              )}

              {/* Diagnostic */}
              {selectedConsultationData.bilan && (
                <div className="bg-red-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-red-900 mb-4">Bilan/Diagnostic</h3>
                  <p className="text-sm text-gray-900 bg-white p-4 rounded-lg leading-relaxed">
                    {selectedConsultationData.bilan}
                  </p>
                </div>
              )}

              {/* Traitement */}
              {selectedConsultationData.traitement && (
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-purple-900 mb-4">Traitement Prescrit</h3>
                  <p className="text-sm text-gray-900 bg-white p-4 rounded-lg leading-relaxed">
                    {selectedConsultationData.traitement}
                  </p>
                </div>
              )}

              {/* Rappel vaccin */}
              {selectedConsultationData.rappel_vaccin && (
                <div className="bg-orange-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-orange-900 mb-4">💉 Rappel Vaccin</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Nom du vaccin</label>
                      <p className="mt-1 text-sm text-gray-900 font-medium">{selectedConsultationData.nom_vaccin || 'Non spécifié'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Date prévue</label>
                      <p className="mt-1 text-sm text-gray-900">
                        {selectedConsultationData.date_vaccin ? new Date(selectedConsultationData.date_vaccin).toLocaleDateString('fr-FR') : 'Non spécifiée'}
                      </p>
                    </div>
                  </div>
                  {selectedConsultationData.rappel_whatsapp_vaccin && (
                    <div className="mt-3 p-3 bg-white rounded-lg">
                      <div className="flex items-center text-green-700">
                        <span className="text-sm">📱 Rappel WhatsApp programmé</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Relance */}
              {selectedConsultationData.relance_date && (
                <div className="bg-indigo-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-indigo-900 mb-4">📅 Relance Programmée</h3>
                  <p className="text-sm text-gray-900">
                    <strong>Date de relance:</strong> {new Date(selectedConsultationData.relance_date).toLocaleDateString('fr-FR')}
                  </p>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowConsultationModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Payment Edit Modal */}
      <PaymentModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        appointment={editingPayment}
        onPaymentUpdate={async (appointmentId, paymentData) => {
          // Reload payments and dashboard data after update
          await fetchPayments();
          await fetchInitialData(); // Reload dashboard stats
          setShowEditModal(false); // Close modal after successful update
          toast.success('Paiement et consultation mis à jour avec succès');
        }}
        API_BASE_URL={API_BASE_URL}
        user={user}
      />
    </div>
  );
};

export default Billing;