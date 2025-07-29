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
  Award
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
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, payments, caisse
  
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
    assure: ''
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0
  });
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

  useEffect(() => {
    fetchInitialData();
    fetchPatients();
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
                    setMonthlyStats(null);
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
                    setYearlyStats(null);
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

        {/* Evolution Graphs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <LineChart className="w-5 h-5 text-blue-500 mr-2" />
            Évolution par mois sur l'année
          </h3>
          
          {evolutionData.length > 0 ? (
            <div className="space-y-8">
              {/* Revenue Evolution Chart */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Évolution de la recette (TND)</h4>
                <div className="h-64 w-full">
                  <svg viewBox="0 0 800 200" className="w-full h-full">
                    {/* Grid lines */}
                    <defs>
                      <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                        <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e5e7eb" strokeWidth="0.5"/>
                      </pattern>
                    </defs>
                    <rect width="800" height="200" fill="url(#grid)" />
                    
                    {/* Line chart */}
                    <polyline
                      fill="none"
                      stroke="#10b981"
                      strokeWidth="3"
                      points={evolutionData.map((data, index) => {
                        const x = (index * 700) / (evolutionData.length - 1) + 50;
                        const maxRevenue = Math.max(...evolutionData.map(d => d.recette));
                        const y = 180 - ((data.recette / maxRevenue) * 160);
                        return `${x},${y}`;
                      }).join(' ')}
                    />
                    
                    {/* Data points */}
                    {evolutionData.map((data, index) => {
                      const x = (index * 700) / (evolutionData.length - 1) + 50;
                      const maxRevenue = Math.max(...evolutionData.map(d => d.recette));
                      const y = 180 - ((data.recette / maxRevenue) * 160);
                      return (
                        <g key={index}>
                          <circle cx={x} cy={y} r="4" fill="#10b981" />
                          <text x={x} y="195" textAnchor="middle" fontSize="12" fill="#6b7280">
                            {data.mois}
                          </text>
                          <text x={x} y={y - 8} textAnchor="middle" fontSize="10" fill="#374151" fontWeight="bold">
                            {Math.round(data.recette)}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </div>

              {/* Consultations Evolution Chart */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Évolution des consultations</h4>
                <div className="h-64 w-full">
                  <svg viewBox="0 0 800 200" className="w-full h-full">
                    <rect width="800" height="200" fill="url(#grid)" />
                    
                    {/* Area chart */}
                    <defs>
                      <linearGradient id="blueGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3"/>
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1"/>
                      </linearGradient>
                    </defs>
                    
                    <polygon 
                      fill="url(#blueGradient)"
                      stroke="#3b82f6"
                      strokeWidth="2"
                      points={`50,180 ${evolutionData.map((data, index) => {
                        const x = (index * 700) / (evolutionData.length - 1) + 50;
                        const maxConsultations = Math.max(...evolutionData.map(d => d.nb_consultations));
                        const y = 180 - ((data.nb_consultations / maxConsultations) * 160);
                        return `${x},${y}`;
                      }).join(' ')} ${(evolutionData.length - 1) * 700 / (evolutionData.length - 1) + 50},180`}
                    />
                    
                    {/* Data points */}
                    {evolutionData.map((data, index) => {
                      const x = (index * 700) / (evolutionData.length - 1) + 50;
                      const maxConsultations = Math.max(...evolutionData.map(d => d.nb_consultations));
                      const y = 180 - ((data.nb_consultations / maxConsultations) * 160);
                      return (
                        <g key={index}>
                          <circle cx={x} cy={y} r="3" fill="#3b82f6" />
                          <text x={x} y="195" textAnchor="middle" fontSize="12" fill="#6b7280">
                            {data.mois}
                          </text>
                          <text x={x} y={y - 8} textAnchor="middle" fontSize="10" fill="#374151" fontWeight="bold">
                            {data.nb_consultations}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </div>

              {/* New Patients Bar Chart */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Évolution des nouveaux patients</h4>
                <div className="h-64 w-full">
                  <svg viewBox="0 0 800 200" className="w-full h-full">
                    <rect width="800" height="200" fill="url(#grid)" />
                    
                    {/* Bar chart */}
                    {evolutionData.map((data, index) => {
                      const barWidth = 700 / evolutionData.length * 0.8;
                      const x = (index * 700) / evolutionData.length + 50 + (700 / evolutionData.length * 0.1);
                      const maxPatients = Math.max(...evolutionData.map(d => d.nouveaux_patients || 0));
                      const barHeight = maxPatients > 0 ? ((data.nouveaux_patients || 0) / maxPatients) * 160 : 0;
                      const y = 180 - barHeight;
                      
                      return (
                        <g key={index}>
                          <rect 
                            x={x} 
                            y={y} 
                            width={barWidth} 
                            height={barHeight} 
                            fill="#f97316"
                            rx="2"
                          />
                          <text x={x + barWidth/2} y="195" textAnchor="middle" fontSize="12" fill="#6b7280">
                            {data.mois}
                          </text>
                          <text x={x + barWidth/2} y={y - 5} textAnchor="middle" fontSize="10" fill="#374151" fontWeight="bold">
                            {data.nouveaux_patients || 0}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
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
                  <BarChart3 className="w-4 h-4 mr-2" />
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
    </div>
  );
};

export default Billing;