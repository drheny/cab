import React, { useState, useEffect, useMemo } from 'react';
import { 
  DollarSign, 
  Search, 
  Download, 
  TrendingUp,
  Users,
  FileText,
  CreditCard,
  Edit,
  Trash2,
  Eye,
  RefreshCw,
  PieChart,
  CheckCircle,
  XCircle,
  X,
  Activity,
  Calendar,
  BarChart3,
  LineChart,
  Star,
  Target,
  Award
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Billing = ({ user }) => {
  // States for data
  const [payments, setPayments] = useState([]);
  const [stats, setStats] = useState({});
  const [advancedStats, setAdvancedStats] = useState({});
  const [enhancedStats, setEnhancedStats] = useState({});
  const [cashMovements, setCashMovements] = useState([]);
  const [cashBalance, setCashBalance] = useState(0);
  const [topPatients, setTopPatients] = useState([]);
  const [evolutionData, setEvolutionData] = useState([]);
  const [predictiveAnalysis, setPredictiveAnalysis] = useState(null);
  
  // States for UI
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, payments, caisse, stats
  const [dateFilter, setDateFilter] = useState({
    debut: new Date().toISOString().split('T')[0].substring(0, 7) + '-01', // First day of current month
    fin: new Date().toISOString().split('T')[0] // Today
  });
  
  // New states for enhanced features
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [dailyPayments, setDailyPayments] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState(null);
  const [yearlyStats, setYearlyStats] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [patientPayments, setPatientPayments] = useState(null);
  const [patients, setPatients] = useState([]);
  
  // States for advanced search
  const [searchFilters, setSearchFilters] = useState({
    patientName: '',
    dateDebut: '',
    dateFin: '',
    statutPaiement: '',
    assure: ''
  });
  
  // Pagination states
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    limit: 20
  });
  
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Advanced stats filters
  const [statsPeriod, setStatsPeriod] = useState('month'); // day, week, month, year
  
  // Modal states
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  
  // Cash movement states
  const [showCashForm, setShowCashForm] = useState(false);
  const [cashForm, setCashForm] = useState({
    montant: '',
    type_mouvement: 'ajout',
    motif: '',
    date: new Date().toISOString().split('T')[0]
  });
  
  // Export modal states
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportOptions, setExportOptions] = useState({
    date: true,
    patient: true,
    montant: true,
    methode: true,
    assurance: true,
    notes: false,
    periode: 'current', // current, custom
    indicateurs: {
      ca: true,
      visites: true,
      controles: true,
      assures: true,
      paiements: true
    }
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchInitialData();
    fetchPatients();
  }, []);

  useEffect(() => {
    if (dateFilter.debut && dateFilter.fin) {
      fetchStats();
      fetchAdvancedStats();
      fetchCashMovements();
    }
  }, [dateFilter, statsPeriod]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchPayments(),
        fetchStats(),
        fetchAdvancedStats(),
        fetchCashMovements(),
        fetchEnhancedStats(),
        fetchTopPatients(),
        fetchEvolutionData(),
        fetchPredictiveAnalysis()
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

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(response.data?.patients || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
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

  const fetchPatientPayments = async (patientId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/facturation/patient-payments`, {
        params: { patient_id: patientId }
      });
      setPatientPayments(response.data);
    } catch (error) {
      console.error('Error fetching patient payments:', error);
      toast.error('Erreur lors du chargement des paiements du patient');
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments`);
      const paymentsData = response.data || [];
      
      setPayments(paymentsData);
    } catch (error) {
      console.error('Error fetching payments:', error);
      toast.error('Erreur lors du chargement des paiements');
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments/stats`, {
        params: {
          date_debut: dateFilter.debut,
          date_fin: dateFilter.fin
        }
      });
      setStats(response.data || {});
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchAdvancedStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments/advanced-stats`, {
        params: {
          period: statsPeriod,
          date_debut: dateFilter.debut,
          date_fin: dateFilter.fin
        }
      });
      setAdvancedStats(response.data || {});
    } catch (error) {
      console.error('Error fetching advanced stats:', error);
    }
  };

  // Filtered payments based on search and filters
  const filteredPayments = useMemo(() => {
    let filtered = [...payments];

    // Date filter
    filtered = filtered.filter(payment => 
      payment.date >= dateFilter.debut && payment.date <= dateFilter.fin
    );

    // Sort by date (most recent first)
    filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

    return filtered;
  }, [payments, dateFilter]);

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
      if (exportOptions.methode) headers.push('Méthode');
      if (exportOptions.assurance) headers.push('Assuré');
      if (exportOptions.notes) headers.push('Notes');
      
      // Prepare data rows
      const csvData = filteredPayments.map(payment => {
        const row = [];
        if (exportOptions.date) row.push(new Date(payment.date).toLocaleDateString('fr-FR'));
        if (exportOptions.patient) row.push(`${payment.patient?.prenom} ${payment.patient?.nom}`);
        if (exportOptions.montant) row.push(`${payment.montant}`);
        if (exportOptions.methode) row.push(payment.type_paiement);
        if (exportOptions.assurance) row.push(payment.assure ? 'Oui' : 'Non');
        if (exportOptions.notes) row.push(payment.notes || '');
        return row;
      });

      // Add enhanced statistics section if requested
      if (Object.values(exportOptions.indicateurs).some(v => v)) {
        csvData.push([]); // Empty row
        csvData.push(['=== STATISTIQUES ENHANCÉES ===']);
        csvData.push([]);
        
        // Enhanced stats
        if (enhancedStats) {
          csvData.push(['Recette du jour:', `${formatCurrency(enhancedStats.recette_jour || 0)}`]);
          csvData.push(['Recette du mois:', `${formatCurrency(enhancedStats.recette_mois || 0)}`]);
          csvData.push(['Recette de l\'année:', `${formatCurrency(enhancedStats.recette_annee || 0)}`]);
          csvData.push(['Nouveaux patients cette année:', enhancedStats.nouveaux_patients_annee || 0]);
          csvData.push([]);
        }
        
        // Legacy stats for compatibility
        if (exportOptions.indicateurs.ca) {
          csvData.push(['Chiffre d\'affaires total:', `${formatCurrency(stats.total_montant || 0)}`]);
        }
        if (exportOptions.indicateurs.paiements) {
          csvData.push(['Nombre de paiements:', stats.nb_paiements || 0]);
        }
        if (exportOptions.indicateurs.visites) {
          csvData.push(['Nombre de visites:', stats.consultations?.nb_visites || 0]);
        }
        if (exportOptions.indicateurs.controles) {
          csvData.push(['Nombre de contrôles:', stats.consultations?.nb_controles || 0]);
        }
        if (exportOptions.indicateurs.assures) {
          csvData.push(['Patients assurés:', stats.consultations?.nb_assures || 0]);
        }
        
        // Add top patients section
        if (topPatients.length > 0) {
          csvData.push([]);
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
        }
        
        // Add evolution data section
        if (evolutionData.length > 0) {
          csvData.push([]);
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
        
        // Add predictive analysis section
        if (predictiveAnalysis) {
          csvData.push([]);
          csvData.push(['=== ANALYSE PRÉDICTIVE ===']);
          csvData.push(['Type d\'analyse:', predictiveAnalysis.generation_method === 'ai' ? 'Intelligence Artificielle' : 'Statistique']);
          csvData.push([]);
          csvData.push(['Analyse:', predictiveAnalysis.ai_analysis]);
          csvData.push([]);
          
          if (predictiveAnalysis.peak_months) {
            csvData.push(['PÉRIODES DE PIC (TOP 3):']);
            csvData.push(['Rang', 'Mois', 'Recette Moyenne (TND)', 'Consultations Moyennes']);
            predictiveAnalysis.peak_months.forEach((month, index) => {
              csvData.push([
                index + 1,
                month.month,
                month.avg_recette.toFixed(2),
                Math.round(month.avg_consultations)
              ]);
            });
            csvData.push([]);
          }
          
          if (predictiveAnalysis.trough_months) {
            csvData.push(['PÉRIODES DE CREUX (BOTTOM 3):']);
            csvData.push(['Rang', 'Mois', 'Recette Moyenne (TND)', 'Consultations Moyennes']);
            predictiveAnalysis.trough_months.forEach((month, index) => {
              csvData.push([
                index + 1,
                month.month,
                month.avg_recette.toFixed(2),
                Math.round(month.avg_consultations)
              ]);
            });
          }
        }
        
        // Add period breakdown if advanced stats are available
        if (advancedStats.breakdown && advancedStats.breakdown.length > 0) {
          csvData.push([]);
          csvData.push([`=== RÉPARTITION PAR ${statsPeriod.toUpperCase()} ===`]);
          csvData.push(['Période', 'CA', 'Paiements', 'Visites', 'Contrôles', 'Assurés']);
          
          advancedStats.breakdown.forEach(period => {
            csvData.push([
              period.periode || period.date,
              period.ca,
              period.nb_paiements,
              period.nb_visites,
              period.nb_controles,
              period.nb_assures
            ]);
          });
        }
      }

      // Create CSV content
      const csvContent = [headers, ...csvData]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');

      // Download file with enhanced filename
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      const today = new Date().toISOString().split('T')[0];
      const filename = `facturation_enhanced_${dateFilter.debut}_${dateFilter.fin}_${today}.csv`;
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

  const handleEditPayment = async (payment) => {
    setEditingPayment(payment);
    setShowEditModal(true);
  };

  const handleAdvancedSearch = async (page = 1) => {
    setIsSearching(true);
    try {
      const params = new URLSearchParams();
      if (searchFilters.patientName) params.append('patient_name', searchFilters.patientName);
      if (searchFilters.dateDebut) params.append('date_debut', searchFilters.dateDebut);
      if (searchFilters.dateFin) params.append('date_fin', searchFilters.dateFin);
      if (searchFilters.statutPaiement) params.append('statut_paiement', searchFilters.statutPaiement);
      if (searchFilters.assure !== '') params.append('assure', searchFilters.assure);
      params.append('page', page.toString());
      params.append('limit', pagination.limit.toString());
      
      const response = await axios.get(`${API_BASE_URL}/api/payments/search?${params.toString()}`);
      const data = response.data;
      
      setSearchResults(data.payments || []);
      setPagination({
        currentPage: data.pagination.current_page,
        totalPages: data.pagination.total_pages,
        totalCount: data.pagination.total_count,
        limit: data.pagination.limit
      });
      
    } catch (error) {
      console.error('Error in advanced search:', error);
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
      assure: ''
    });
    setSearchResults([]);
    setPagination({
      currentPage: 1,
      totalPages: 1,
      totalCount: 0,
      limit: 20
    });
  };

  const handleDeletePayment = async (payment) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer ce paiement de ${payment.patient?.prenom} ${payment.patient?.nom} ?`)) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/payments/${payment.id}`);
      
      toast.success('Paiement supprimé avec succès');
      
      // Refresh data
      await Promise.all([
        fetchPayments(),
        fetchStats(),
        fetchAdvancedStats()
      ]);
      
      // Refresh search results if searching
      if (searchResults.length > 0) {
        handleAdvancedSearch(pagination.currentPage);
      }
      
    } catch (error) {
      console.error('Error deleting payment:', error);
      toast.error('Erreur lors de la suppression du paiement');
    }
  };

  const handleUpdatePayment = async (paymentId, updatedData) => {
    try {
      const paymentData = {
        paye: updatedData.paye,
        montant: updatedData.montant,
        type_paiement: 'espece', // Toujours espèces
        assure: updatedData.assure,
        notes: updatedData.notes || ''
      };

      await axios.put(`${API_BASE_URL}/api/payments/${paymentId}`, paymentData);
      
      toast.success('Paiement mis à jour avec succès');
      
      // Refresh data
      await Promise.all([
        fetchPayments(),
        fetchStats()
      ]);
      
      setShowEditModal(false);
      setEditingPayment(null);
      
    } catch (error) {
      console.error('Error updating payment:', error);
      toast.error('Erreur lors de la mise à jour du paiement');
    }
  };

  // Fonctions pour la gestion de caisse
  const fetchCashMovements = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/cash-movements`, {
        params: {
          date_debut: dateFilter.debut,
          date_fin: dateFilter.fin
        }
      });
      setCashMovements(response.data.movements || []);
      setCashBalance(response.data.solde_jour || 0);
    } catch (error) {
      console.error('Error fetching cash movements:', error);
      toast.error('Erreur lors du chargement des mouvements de caisse');
    }
  };

  const handleCreateCashMovement = async () => {
    try {
      if (!cashForm.montant || !cashForm.motif) {
        toast.error('Veuillez remplir tous les champs obligatoires');
        return;
      }

      await axios.post(`${API_BASE_URL}/api/cash-movements`, {
        montant: parseFloat(cashForm.montant),
        type_mouvement: cashForm.type_mouvement,
        motif: cashForm.motif,
        date: cashForm.date
      });

      toast.success('Mouvement de caisse ajouté avec succès');
      
      // Reset form
      setCashForm({
        montant: '',
        type_mouvement: 'ajout',
        motif: '',
        date: new Date().toISOString().split('T')[0]
      });
      
      // Refresh data
      await fetchCashMovements();
      setShowCashForm(false);
      
    } catch (error) {
      console.error('Error creating cash movement:', error);
      toast.error('Erreur lors de la création du mouvement de caisse');
    }
  };

  const handleDeleteCashMovement = async (movementId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce mouvement de caisse ?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE_URL}/api/cash-movements/${movementId}`);
      toast.success('Mouvement de caisse supprimé avec succès');
      await fetchCashMovements();
    } catch (error) {
      console.error('Error deleting cash movement:', error);
      toast.error('Erreur lors de la suppression du mouvement de caisse');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-TN', {
      style: 'decimal',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0) + ' TND';
  };

  const getPaymentMethodIcon = (method) => {
    switch (method) {
      case 'carte': return <CreditCard className="w-4 h-4" />;
      case 'espece': return <DollarSign className="w-4 h-4" />;
      case 'cheque': return <FileText className="w-4 h-4" />;
      case 'virement': return <TrendingUp className="w-4 h-4" />;
      case 'gratuit': return <CheckCircle className="w-4 h-4" />;
      default: return <DollarSign className="w-4 h-4" />;
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

      {/* Date Range Filter - Simplified */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Du</label>
              <input
                type="date"
                value={dateFilter.debut}
                onChange={(e) => setDateFilter(prev => ({ ...prev, debut: e.target.value }))}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Au</label>
              <input
                type="date"
                value={dateFilter.fin}
                onChange={(e) => setDateFilter(prev => ({ ...prev, fin: e.target.value }))}
                className="input-field"
              />
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Période de filtrage</div>
            <div className="font-medium">
              {new Date(dateFilter.debut).toLocaleDateString('fr-FR')} - {new Date(dateFilter.fin).toLocaleDateString('fr-FR')}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'dashboard', label: 'Tableau de bord', icon: PieChart },
            { id: 'payments', label: 'Historique paiements', icon: CreditCard },
            { id: 'caisse', label: 'Caisse', icon: DollarSign },
            { id: 'stats', label: 'Statistiques avancées', icon: BarChart3 }
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

      {/* Enhanced Statistics Cards */}
      {activeTab === 'dashboard' && (
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
      )}

      {/* Enhanced Payment History Section */}
      {activeTab === 'dashboard' && (
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
                      setMonthlyStats(null); // Reset previous data
                      fetchMonthlyStats(parseInt(year), parseInt(month));
                    }}
                    className="input-field w-full"
                  />
                  <div className="text-xs text-blue-600">
                    Stats avec % évolution
                  </div>
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
                      setYearlyStats(null); // Reset previous data
                      fetchYearlyStats(parseInt(e.target.value));
                    }}
                    className="input-field w-full"
                  />
                  <div className="text-xs text-purple-600">
                    Stats annuelles complètes
                  </div>
                </div>
              </div>
            </div>

            {/* Daily Results */}
            {dailyPayments && (
              <div className="border-t pt-6">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <Calendar className="w-5 h-5 text-green-500 mr-2" />
                  Résultats du {new Date(dailyPayments.date).toLocaleDateString('fr-FR')}
                </h4>
                
                {/* Daily Stats Summary */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                  <div className="bg-green-50 p-4 rounded-lg text-center">
                    <div className="text-sm text-green-600 font-medium">Recette totale</div>
                    <div className="text-xl font-bold text-green-700">
                      {formatCurrency(dailyPayments.totals.recette_totale)}
                    </div>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg text-center">
                    <div className="text-sm text-blue-600 font-medium">Visites</div>
                    <div className="text-xl font-bold text-blue-700">
                      {dailyPayments.totals.nb_visites}
                    </div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg text-center">
                    <div className="text-sm text-purple-600 font-medium">Contrôles</div>
                    <div className="text-xl font-bold text-purple-700">
                      {dailyPayments.totals.nb_controles}
                    </div>
                  </div>
                  <div className="bg-indigo-50 p-4 rounded-lg text-center">
                    <div className="text-sm text-indigo-600 font-medium">Assurés</div>
                    <div className="text-xl font-bold text-indigo-700">
                      {dailyPayments.totals.nb_assures}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-sm text-gray-600 font-medium">Total</div>
                    <div className="text-xl font-bold text-gray-700">
                      {dailyPayments.totals.nb_total}
                    </div>
                  </div>
                </div>

                {/* Daily Patients List */}
                {dailyPayments.payments.length > 0 ? (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-3">
                      Liste des patients ({dailyPayments.payments.length})
                    </h5>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-white">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type visite</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Montant</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut paiement</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assuré</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {dailyPayments.payments.map((payment, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-4 py-3 font-medium text-gray-900">
                                {payment.patient?.prenom} {payment.patient?.nom}
                              </td>
                              <td className="px-4 py-3">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  payment.type_visite === 'visite' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'
                                }`}>
                                  {payment.type_visite === 'visite' ? 'Visite' : 'Contrôle'}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-semibold text-green-600">
                                {formatCurrency(payment.montant)}
                              </td>
                              <td className="px-4 py-3">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Payé
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  payment.assure ? 'bg-indigo-100 text-indigo-800' : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {payment.assure ? 'Oui' : 'Non'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
                    <Calendar className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p>Aucun paiement pour cette date</p>
                  </div>
                )}
              </div>
            )}

            {/* Monthly Results */}
            {monthlyStats && (
              <div className="border-t pt-6">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <Calendar className="w-5 h-5 text-blue-500 mr-2" />
                  Statistiques de {monthlyStats.month}/{monthlyStats.year}
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="bg-blue-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-blue-600 font-medium mb-2">Recette du mois</div>
                    <div className="text-2xl font-bold text-blue-700">
                      {formatCurrency(monthlyStats.recette_mois)}
                    </div>
                    {monthlyStats.evolution && (
                      <div className="text-xs mt-2 flex items-center justify-center">
                        {monthlyStats.evolution.evolution_pourcentage >= 0 ? (
                          <span className="text-green-600 flex items-center">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            +{monthlyStats.evolution.evolution_pourcentage}%
                          </span>
                        ) : (
                          <span className="text-red-600 flex items-center">
                            <TrendingUp className="w-3 h-3 mr-1 rotate-180" />
                            {monthlyStats.evolution.evolution_pourcentage}%
                          </span>
                        )}
                        <span className="text-gray-500 ml-1">vs {monthlyStats.evolution.mois_precedent}</span>
                      </div>
                    )}
                  </div>
                  <div className="bg-green-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-green-600 font-medium mb-2">Visites</div>
                    <div className="text-2xl font-bold text-green-700">{monthlyStats.nb_visites}</div>
                  </div>
                  <div className="bg-purple-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-purple-600 font-medium mb-2">Contrôles</div>
                    <div className="text-2xl font-bold text-purple-700">{monthlyStats.nb_controles}</div>
                  </div>
                  <div className="bg-indigo-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-indigo-600 font-medium mb-2">Assurés</div>
                    <div className="text-2xl font-bold text-indigo-700">{monthlyStats.nb_assures}</div>
                    <div className="text-xs text-indigo-500 mt-1">
                      sur {monthlyStats.nb_total_rdv} RDV
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Yearly Results */}
            {yearlyStats && (
              <div className="border-t pt-6">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <Calendar className="w-5 h-5 text-purple-500 mr-2" />
                  Statistiques de {yearlyStats.year}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-purple-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-purple-600 font-medium mb-2">Recette totale</div>
                    <div className="text-3xl font-bold text-purple-700">
                      {formatCurrency(yearlyStats.recette_annee)}
                    </div>
                  </div>
                  <div className="bg-green-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-green-600 font-medium mb-2">Total visites</div>
                    <div className="text-3xl font-bold text-green-700">{yearlyStats.nb_visites}</div>
                  </div>
                  <div className="bg-indigo-50 p-6 rounded-lg text-center">
                    <div className="text-sm text-indigo-600 font-medium mb-2">Patients assurés</div>
                    <div className="text-3xl font-bold text-indigo-700">{yearlyStats.nb_assures}</div>
                    <div className="text-xs text-indigo-500 mt-1">
                      sur {yearlyStats.nb_total_rdv} RDV
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Advanced Statistics Tab */}
      {activeTab === 'stats' && (
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
                <Star className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p>Aucune donnée de patients disponible</p>
              </div>
            )}
          </div>

          {/* Evolution Graphs */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <LineChart className="w-5 h-5 text-blue-500 mr-2" />
              Évolution par mois sur l'année
            </h3>
            
            {evolutionData.length > 0 ? (
              <div className="space-y-6">
                {/* Revenue Evolution */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Évolution de la recette</h4>
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-2">
                    {evolutionData.map((data, index) => (
                      <div key={index} className="text-center">
                        <div className="mb-2">
                          <div 
                            className="bg-green-500 rounded-t"
                            style={{ 
                              height: `${Math.max(20, (data.recette / Math.max(...evolutionData.map(d => d.recette))) * 100)}px`,
                              minHeight: '20px'
                            }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-600">
                          {data.mois}
                        </div>
                        <div className="text-xs font-medium text-green-600">
                          {formatCurrency(data.recette).replace(' TND', '')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Consultations Evolution */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Évolution des consultations</h4>
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-2">
                    {evolutionData.map((data, index) => (
                      <div key={index} className="text-center">
                        <div className="mb-2">
                          <div 
                            className="bg-blue-500 rounded-t"
                            style={{ 
                              height: `${Math.max(20, (data.nb_consultations / Math.max(...evolutionData.map(d => d.nb_consultations))) * 100)}px`,
                              minHeight: '20px'
                            }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-600">
                          {data.mois}
                        </div>
                        <div className="text-xs font-medium text-blue-600">
                          {data.nb_consultations}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* New Patients Evolution */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Évolution des nouveaux patients</h4>
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-2">
                    {evolutionData.map((data, index) => (
                      <div key={index} className="text-center">
                        <div className="mb-2">
                          <div 
                            className="bg-orange-500 rounded-t"
                            style={{ 
                              height: `${Math.max(20, (data.nouveaux_patients / Math.max(...evolutionData.map(d => d.nouveaux_patients || 0))) * 100)}px`,
                              minHeight: '20px'
                            }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-600">
                          {data.mois}
                        </div>
                        <div className="text-xs font-medium text-orange-600">
                          {data.nouveaux_patients || 0}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p>Aucune donnée d'évolution disponible</p>
              </div>
            )}
          </div>

          {/* Predictive Analysis */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Target className="w-5 h-5 text-purple-500 mr-2" />
              Analyse et prédiction des périodes de pics et de creux
            </h3>
            
            {predictiveAnalysis ? (
              <div className="space-y-6">
                {/* AI Analysis */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-2 flex items-center">
                    <Activity className="w-4 h-4 mr-2" />
                    Analyse {predictiveAnalysis.generation_method === 'ai' ? 'IA' : 'Statistique'}
                  </h4>
                  <p className="text-purple-800 text-sm leading-relaxed">
                    {predictiveAnalysis.ai_analysis}
                  </p>
                </div>

                {/* Peak and Trough Periods */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Peak Months */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                      <TrendingUp className="w-4 h-4 text-green-500 mr-2" />
                      Périodes de pic (Top 3)
                    </h4>
                    <div className="space-y-2">
                      {predictiveAnalysis.peak_months?.map((month, index) => (
                        <div
                          key={month.month}
                          className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg"
                        >
                          <div className="flex items-center space-x-2">
                            <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                              {index + 1}
                            </div>
                            <span className="font-medium text-green-900">
                              Mois {month.month}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-600">
                              {formatCurrency(month.avg_recette)}
                            </div>
                            <div className="text-xs text-green-600">
                              {Math.round(month.avg_consultations)} consult./mois
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Trough Months */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                      <TrendingUp className="w-4 h-4 text-red-500 mr-2 rotate-180" />
                      Périodes de creux (Bottom 3)
                    </h4>
                    <div className="space-y-2">
                      {predictiveAnalysis.trough_months?.map((month, index) => (
                        <div
                          key={month.month}
                          className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg"
                        >
                          <div className="flex items-center space-x-2">
                            <div className="w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                              {index + 1}
                            </div>
                            <span className="font-medium text-red-900">
                              Mois {month.month}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-red-600">
                              {formatCurrency(month.avg_recette)}
                            </div>
                            <div className="text-xs text-red-600">
                              {Math.round(month.avg_consultations)} consult./mois
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Monthly Averages Chart */}
                {predictiveAnalysis.monthly_averages && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Moyennes mensuelles</h4>
                    <div className="grid grid-cols-12 gap-1">
                      {predictiveAnalysis.monthly_averages.map((data) => (
                        <div key={data.month} className="text-center">
                          <div className="mb-2">
                            <div 
                              className="bg-purple-500 rounded-t"
                              style={{ 
                                height: `${Math.max(20, (data.avg_recette / Math.max(...predictiveAnalysis.monthly_averages.map(d => d.avg_recette))) * 80)}px`,
                                minHeight: '20px'
                              }}
                            ></div>
                          </div>
                          <div className="text-xs text-gray-600">{data.month}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Target className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                <p>Analyse prédictive en cours de chargement...</p>
                <button
                  onClick={fetchPredictiveAnalysis}
                  className="btn-primary mt-4"
                >
                  Charger l'analyse
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Payments Tab */}
      {activeTab === 'payments' && (
        <div className="space-y-6">
          {/* Advanced Search Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recherche avancée</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-4">
              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom du patient</label>
                <input
                  type="text"
                  placeholder="Nom ou prénom..."
                  value={searchFilters.patientName}
                  onChange={(e) => setSearchFilters(prev => ({
                    ...prev,
                    patientName: e.target.value
                  }))}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date début</label>
                <input
                  type="date"
                  value={searchFilters.dateDebut}
                  onChange={(e) => setSearchFilters(prev => ({
                    ...prev,
                    dateDebut: e.target.value
                  }))}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date fin</label>
                <input
                  type="date"
                  value={searchFilters.dateFin}
                  onChange={(e) => setSearchFilters(prev => ({
                    ...prev,
                    dateFin: e.target.value
                  }))}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Statut paiement</label>
                <select
                  value={searchFilters.statutPaiement}
                  onChange={(e) => setSearchFilters(prev => ({
                    ...prev,
                    statutPaiement: e.target.value
                  }))}
                  className="input-field"
                >
                  <option value="">Tous</option>
                  <option value="visite">Visite</option>
                  <option value="controle">Contrôle gratuit</option>
                  <option value="impaye">Impayé</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assurance</label>
                <select
                  value={searchFilters.assure}
                  onChange={(e) => setSearchFilters(prev => ({
                    ...prev,
                    assure: e.target.value
                  }))}
                  className="input-field"
                >
                  <option value="">Tous</option>
                  <option value="true">Assurés</option>
                  <option value="false">Non assurés</option>
                </select>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleAdvancedSearch(1)}
                disabled={isSearching}
                className="btn-primary flex items-center space-x-2"
              >
                <Search className="w-4 h-4" />
                <span>{isSearching ? 'Recherche...' : 'Rechercher'}</span>
              </button>
              <button
                onClick={clearAdvancedSearch}
                className="btn-outline flex items-center space-x-2"
              >
                <X className="w-4 h-4" />
                <span>Effacer</span>
              </button>
              {searchResults.length > 0 && (
                <span className="text-sm text-gray-600">
                  {pagination.totalCount} résultat(s) trouvé(s)
                </span>
              )}
            </div>
          </div>

          {/* Results Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Patient
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Montant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Statut paiement
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Assurance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(searchResults.length > 0 ? searchResults : filteredPayments).map((payment) => (
                    <tr key={payment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(payment.date).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {payment.patient?.prenom} {payment.patient?.nom}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {payment.appointment_id}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">
                          {formatCurrency(payment.montant)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {/* Déterminer le statut du paiement */}
                        {payment.statut === 'paye' ? (
                          payment.type_rdv === 'controle' ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                              Contrôle
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Visite
                            </span>
                          )
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Impayé
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {payment.assure ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Assuré
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Non assuré
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setSelectedPayment(payment);
                              setShowPaymentModal(true);
                            }}
                            className="text-indigo-600 hover:text-indigo-900"
                            title="Voir les détails"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleEditPayment(payment)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Modifier le paiement"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleDeletePayment(payment)}
                            className="text-red-600 hover:text-red-900"
                            title="Supprimer le paiement"
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
          </div>

          {/* Pagination */}
          {searchResults.length > 0 && pagination.totalPages > 1 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Page {pagination.currentPage} sur {pagination.totalPages} 
                  ({pagination.totalCount} résultats au total)
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleAdvancedSearch(pagination.currentPage - 1)}
                    disabled={!pagination.currentPage > 1 || isSearching}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                  >
                    Précédent
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                    const pageNum = Math.max(1, pagination.currentPage - 2) + i;
                    if (pageNum <= pagination.totalPages) {
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handleAdvancedSearch(pageNum)}
                          disabled={isSearching}
                          className={`px-3 py-1 text-sm rounded-lg ${
                            pageNum === pagination.currentPage
                              ? 'bg-primary-500 text-white'
                              : 'border border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    }
                    return null;
                  })}
                  
                  <button
                    onClick={() => handleAdvancedSearch(pagination.currentPage + 1)}
                    disabled={pagination.currentPage >= pagination.totalPages || isSearching}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                  >
                    Suivant
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Empty States */}
          {searchResults.length === 0 && filteredPayments.length === 0 && !isSearching && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun paiement trouvé pour les critères sélectionnés</p>
            </div>
          )}
          
          {isSearching && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
              <p className="text-gray-500">Recherche en cours...</p>
            </div>
          )}
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
                {cashMovements.length} mouvement(s) pour la période sélectionnée
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
              <p className="text-gray-500">Aucun mouvement de caisse pour la période sélectionnée</p>
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
                  <label className="block text-sm font-medium text-gray-700">Méthode</label>
                  <p className="text-sm text-gray-900 capitalize">
                    {selectedPayment.type_paiement}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Assurance</label>
                  <p className="text-sm text-gray-900">
                    {selectedPayment.assure ? 'Assuré' : 'Non assuré'}
                  </p>
                </div>
                
                {selectedPayment.notes && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Notes</label>
                    <p className="text-sm text-gray-900">{selectedPayment.notes}</p>
                  </div>
                )}
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

      {/* Payment Edit Modal */}
      {showEditModal && editingPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Modifier le paiement</h3>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingPayment(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const updatedData = {
                  paye: true, // Toujours payé si on édite
                  montant: parseFloat(formData.get('montant')) || 0,
                  assure: formData.get('assure') === 'on',
                  notes: formData.get('notes') || ''
                };
                handleUpdatePayment(editingPayment.id, updatedData);
              }}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="edit_montant" className="block text-sm font-medium text-gray-700 mb-2">
                      Montant (TND)
                    </label>
                    <input
                      type="number"
                      id="edit_montant"
                      name="montant"
                      step="0.01"
                      min="0"
                      defaultValue={editingPayment.montant}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Méthode de paiement
                    </label>
                    <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700">
                      💵 Espèces (TND)
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="edit_assure"
                        name="assure"
                        defaultChecked={editingPayment.assure}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor="edit_assure" className="text-sm font-medium text-gray-700">
                        Patient assuré
                      </label>
                    </div>
                  </div>

                  <div>
                    <label htmlFor="edit_notes" className="block text-sm font-medium text-gray-700 mb-2">
                      Notes (optionnel)
                    </label>
                    <textarea
                      id="edit_notes"
                      name="notes"
                      rows="3"
                      defaultValue={editingPayment.notes || ''}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Notes sur le paiement..."
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingPayment(null);
                    }}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                  >
                    Sauvegarder
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Custom Export Modal */}
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
                {/* Champs à inclure */}
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
                        checked={exportOptions.methode}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          methode: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Méthode de paiement</span>
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
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.notes}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          notes: e.target.checked
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Notes</span>
                    </label>
                  </div>
                </div>

                {/* Indicateurs statistiques */}
                <div>
                  <h4 className="text-md font-semibold text-gray-900 mb-3">Indicateurs statistiques</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs.ca}
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
                        checked={exportOptions.indicateurs.visites}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, visites: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Nombre de visites</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs.controles}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, controles: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Nombre de contrôles</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs.assures}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, assures: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Nombre d'assurés</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.indicateurs.paiements}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          indicateurs: { ...prev.indicateurs, paiements: e.target.checked }
                        }))}
                        className="mr-2"
                      />
                      <span className="text-sm">Nombre de paiements</span>
                    </label>
                  </div>
                </div>

                {/* Période */}
                <div>
                  <h4 className="text-md font-semibold text-gray-900 mb-3">Période d'export</h4>
                  <div className="text-sm text-gray-600 mb-2">
                    Du {new Date(dateFilter.debut).toLocaleDateString('fr-FR')} au {new Date(dateFilter.fin).toLocaleDateString('fr-FR')}
                  </div>
                  <div className="text-sm text-gray-500">
                    Analyse par {statsPeriod === 'day' ? 'jour' : statsPeriod === 'week' ? 'semaine' : statsPeriod === 'month' ? 'mois' : 'année'}
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
    </div>
  );
};

export default Billing;