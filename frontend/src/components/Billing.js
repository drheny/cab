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

  // Add real-time patient search effect
  useEffect(() => {
    if (searchFilters.patientName) {
      // Real-time patient search with debounce
      const timer = setTimeout(() => {
        // Filter payments in real-time based on patient name
        const filtered = payments.filter(payment => {
          const fullName = `${payment.patient?.prenom || ''} ${payment.patient?.nom || ''}`.toLowerCase();
          return fullName.includes(searchFilters.patientName.toLowerCase());
        });
        // You could set a separate state for real-time results if needed
      }, 300); // 300ms debounce

      return () => clearTimeout(timer);
    }
  }, [searchFilters.patientName, payments]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchEnhancedStats(),
        fetchTopPatients(),
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

  const fetchTopPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/top-patients?limit=10`);
      setTopPatients(response.data?.top_patients || []);
    } catch (error) {
      console.error('Error fetching top patients:', error);
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
      const response = await axios.get(`${API_BASE_URL}/api/facturation/predictive-analysis`);
      setPredictiveAnalysis(response.data);
    } catch (error) {
      console.error('Error fetching predictive analysis:', error);
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments`);
      setPayments(response.data?.payments || []);
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
    setEditingPayment(payment);
    setShowEditModal(true);
  };

  const handleDeletePayment = async (payment) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce paiement ?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/payments/${payment.id}`);
        toast.success('Paiement supprimé avec succès');
        fetchPayments();
      } catch (error) {
        console.error('Error deleting payment:', error);
        toast.error('Erreur lors de la suppression');
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
      
      // Add top patients section if available
      if (topPatients.length > 0) {
        csvData.push(['=== TOP 10 PATIENTS LES PLUS RENTABLES ===']);
        csvData.push(['Rang', 'Patient', 'Total Payé (TND)', 'Nb Paiements', 'Moyenne']);
        topPatients.forEach((patient, index) => {
          csvData.push([
            index + 1,
            `${patient.patient.prenom} ${patient.patient.nom}`,
            patient.total_montant,
            patient.nb_payments,
            patient.moyenne_paiement.toFixed(2)
          ]);
        });
        csvData.push([]);
      }
      
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
        payment.type_consultation === searchFilters.typeConsultation;
      
      return matchesName && matchesStatus && matchesAssurance && matchesType;
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
        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchInitialData()}
            className="btn-outline flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
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
                      <div className="text-2xl font-bold text-green-700">{dailyPayments.totals.nb_controles}</div>
                      <div className="text-sm text-green-600">Contrôles</div>
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
                      <div className="text-2xl font-bold text-blue-700">{monthlyStats.nb_controles}</div>
                      <div className="text-sm text-blue-600">Contrôles</div>
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
                      <div className="text-2xl font-bold text-purple-700">{yearlyStats.nb_controles}</div>
                      <div className="text-sm text-purple-600">Contrôles</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Advanced Statistics Section */}
          <div className="space-y-6">
            {/* Top 10 Profitable Patients */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Award className="w-5 h-5 text-yellow-500 mr-2" />
                  Top 10 patients les plus rentables
                </h3>
                <button
                  onClick={fetchTopPatients}
                  className="btn-outline text-sm"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Actualiser
                </button>
              </div>
              
              {topPatients.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {topPatients.map((patient, index) => (
                    <div
                      key={patient.patient.id}
                      className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                          index === 0 ? 'bg-yellow-500' : 
                          index === 1 ? 'bg-gray-400' : 
                          index === 2 ? 'bg-orange-500' : 'bg-blue-500'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">
                            {patient.patient.prenom} {patient.patient.nom}
                          </div>
                          <div className="text-sm text-gray-600">
                            {patient.nb_payments} paiement{patient.nb_payments > 1 ? 's' : ''}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-green-600">
                          {formatCurrency(patient.total_montant)}
                        </div>
                        <div className="text-xs text-gray-500">
                          Moy: {formatCurrency(patient.moyenne_paiement)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Award className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <p>Aucune donnée de patients disponible</p>
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
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-4">
              <input
                type="text"
                placeholder="Recherche patient en temps réel..."
                value={searchFilters.patientName}
                onChange={(e) => setSearchFilters(prev => ({ ...prev, patientName: e.target.value }))}
                className="input-field"
              />
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Date début</label>
                <input
                  type="date"
                  value={searchFilters.dateDebut}
                  onChange={(e) => setSearchFilters(prev => ({ ...prev, dateDebut: e.target.value }))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Date fin</label>
                <input
                  type="date"
                  value={searchFilters.dateFin}
                  onChange={(e) => setSearchFilters(prev => ({ ...prev, dateFin: e.target.value }))}
                  className="input-field"
                />
              </div>
              <select
                value={searchFilters.typeConsultation}
                onChange={(e) => setSearchFilters(prev => ({ ...prev, typeConsultation: e.target.value }))}
                className="input-field"
              >
                <option value="">Tous les types</option>
                <option value="visite">Visite</option>
                <option value="controle">Contrôle</option>
              </select>
              <select
                value={searchFilters.statutPaiement}
                onChange={(e) => setSearchFilters(prev => ({ ...prev, statutPaiement: e.target.value }))}
                className="input-field"
              >
                <option value="">Tous les statuts</option>
                <option value="paye">Payé</option>
                <option value="impaye">Impayé</option>
              </select>
              <select
                value={searchFilters.assure}
                onChange={(e) => setSearchFilters(prev => ({ ...prev, assure: e.target.value }))}
                className="input-field"
              >
                <option value="">Assurance</option>
                <option value="true">Assuré</option>
                <option value="false">Non assuré</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {filteredPayments.length} paiement{filteredPayments.length !== 1 ? 's' : ''} trouvé{filteredPayments.length !== 1 ? 's' : ''}
              </div>
              <div className="flex items-center space-x-3">
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
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Patient
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Montant
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredPayments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="text-sm font-medium text-gray-900">
                              {payment.patient?.prenom} {payment.patient?.nom}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(payment.date).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                          {formatCurrency(payment.montant)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            payment.statut === 'paye' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {payment.statut === 'paye' ? 'Payé' : 'Impayé'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleViewPayment(payment)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEditPayment(payment)}
                              className="text-green-600 hover:text-green-900"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeletePayment(payment)}
                              className="text-red-600 hover:text-red-900"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun paiement trouvé</h3>
                <p className="text-gray-500">Aucun paiement ne correspond à vos critères de recherche.</p>
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
    </div>
  );
};

export default Billing;