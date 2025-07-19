import React, { useState, useEffect, useMemo } from 'react';
import { 
  DollarSign, 
  Calendar, 
  Search, 
  Download, 
  TrendingUp,
  Users,
  FileText,
  Filter,
  CreditCard,
  AlertTriangle,
  Edit,
  Trash2,
  Eye,
  RefreshCw,
  PieChart,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  Phone,
  Euro
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Billing = ({ user }) => {
  // States for data
  const [payments, setPayments] = useState([]);
  const [unpaidAppointments, setUnpaidAppointments] = useState([]);
  const [stats, setStats] = useState({});
  const [patients, setPatients] = useState([]);
  
  // States for UI
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, payments, unpaid
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState({
    debut: new Date().toISOString().split('T')[0].substring(0, 7) + '-01', // First day of current month
    fin: new Date().toISOString().split('T')[0] // Today
  });
  const [methodFilter, setMethodFilter] = useState('');
  const [assureFilter, setAssureFilter] = useState('');
  
  // Modal states
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (dateFilter.debut && dateFilter.fin) {
      fetchStats();
    }
  }, [dateFilter]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchPayments(),
        fetchUnpaidAppointments(),
        fetchPatients(),
        fetchStats()
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
      const paymentsData = response.data || [];
      
      // Enrich payments with patient info
      const enrichedPayments = await Promise.all(
        paymentsData.map(async (payment) => {
          try {
            const patientResponse = await axios.get(`${API_BASE_URL}/api/patients/${payment.patient_id}`);
            return {
              ...payment,
              patient: patientResponse.data
            };
          } catch (error) {
            return {
              ...payment,
              patient: { nom: 'Inconnu', prenom: '' }
            };
          }
        })
      );
      
      setPayments(enrichedPayments);
    } catch (error) {
      console.error('Error fetching payments:', error);
      toast.error('Erreur lors du chargement des paiements');
    }
  };

  const fetchUnpaidAppointments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments/unpaid`);
      setUnpaidAppointments(response.data || []);
    } catch (error) {
      console.error('Error fetching unpaid appointments:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients`);
      setPatients(response.data.patients || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
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

  // Filtered payments based on search and filters
  const filteredPayments = useMemo(() => {
    let filtered = [...payments];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(payment => {
        const fullName = `${payment.patient?.prenom} ${payment.patient?.nom}`.toLowerCase();
        return fullName.includes(searchTerm.toLowerCase()) ||
               payment.appointment_id.toLowerCase().includes(searchTerm.toLowerCase());
      });
    }

    // Date filter
    filtered = filtered.filter(payment => 
      payment.date >= dateFilter.debut && payment.date <= dateFilter.fin
    );

    // Method filter
    if (methodFilter) {
      filtered = filtered.filter(payment => payment.type_paiement === methodFilter);
    }

    // Insurance filter
    if (assureFilter !== '') {
      const isAssured = assureFilter === 'true';
      filtered = filtered.filter(payment => payment.assure === isAssured);
    }

    // Sort by date (most recent first)
    filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

    return filtered;
  }, [payments, searchTerm, dateFilter, methodFilter, assureFilter]);

  const exportToExcel = () => {
    // Create CSV data
    const headers = ['Date', 'Patient', 'Montant', 'Méthode', 'Assuré', 'Taux Remb.', 'Notes'];
    const csvData = filteredPayments.map(payment => [
      payment.date,
      `${payment.patient?.prenom} ${payment.patient?.nom}`,
      `${payment.montant} TND`,
      payment.type_paiement,
      payment.assure ? 'Oui' : 'Non',
      `${payment.taux_remboursement || 0}%`,
      payment.notes || ''
    ]);

    const csvContent = [headers, ...csvData]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `paiements_${dateFilter.debut}_${dateFilter.fin}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('Export CSV téléchargé avec succès');
  };

  const handleMarkAsPaid = async (appointment) => {
    try {
      // Calculer le montant par défaut (300 pour visite)
      const defaultAmount = appointment.type_rdv === 'visite' ? 300 : 0;
      
      const paymentData = {
        paye: true,
        montant: defaultAmount,
        type_paiement: 'espece',
        assure: false,
        taux_remboursement: 0,
        notes: 'Marqué comme payé depuis la facturation'
      };

      await axios.put(`${API_BASE_URL}/api/rdv/${appointment.id}/paiement`, paymentData);
      
      toast.success('Paiement marqué comme payé');
      
      // Refresh data
      await Promise.all([
        fetchPayments(),
        fetchUnpaidAppointments(),
        fetchStats()
      ]);
      
    } catch (error) {
      console.error('Error marking as paid:', error);
      toast.error('Erreur lors de la mise à jour du paiement');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-TN', {
      style: 'currency',
      currency: 'TND',
      minimumFractionDigits: 2
    }).format(amount || 0);
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

      {/* Date Range Filter */}
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
            <div className="text-sm text-gray-600">Période sélectionnée</div>
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
            { id: 'unpaid', label: 'Impayés', icon: AlertTriangle }
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
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">CA Période</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(stats.total_montant)}
                  </p>
                </div>
                <div className="p-2 bg-green-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">CA Aujourd'hui</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(stats.ca_jour)}
                  </p>
                </div>
                <div className="p-2 bg-blue-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Nb Paiements</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.nb_paiements || 0}
                  </p>
                </div>
                <div className="p-2 bg-purple-100 rounded-lg">
                  <CreditCard className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Impayés</p>
                  <p className="text-2xl font-bold text-red-600">
                    {unpaidAppointments.length}
                  </p>
                </div>
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Payment Methods Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Méthodes de paiement</h3>
              <div className="space-y-3">
                {Object.entries(stats.by_method || {}).map(([method, data]) => (
                  <div key={method} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getPaymentMethodIcon(method)}
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {method}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatCurrency(data.total)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {data.count} paiements
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Statut assurance</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-sm font-medium text-gray-700">Assurés</span>
                  </div>
                  <span className="text-lg font-bold text-green-600">
                    {stats.assurance?.assures || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <XCircle className="w-5 h-5 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Non assurés</span>
                  </div>
                  <span className="text-lg font-bold text-gray-600">
                    {stats.assurance?.non_assures || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payments Tab */}
      {activeTab === 'payments' && (
        <div className="space-y-6">
          {/* Search and Filters */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Rechercher un patient..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 input-field"
                />
              </div>
              
              <select
                value={methodFilter}
                onChange={(e) => setMethodFilter(e.target.value)}
                className="input-field"
              >
                <option value="">Toutes les méthodes</option>
                <option value="espece">Espèces</option>
                <option value="carte">Carte bancaire</option>
                <option value="cheque">Chèque</option>
                <option value="virement">Virement</option>
                <option value="gratuit">Gratuit</option>
              </select>

              <select
                value={assureFilter}
                onChange={(e) => setAssureFilter(e.target.value)}
                className="input-field"
              >
                <option value="">Tous les patients</option>
                <option value="true">Assurés</option>
                <option value="false">Non assurés</option>
              </select>

              <div className="text-sm text-gray-500 flex items-center">
                {filteredPayments.length} paiement(s) trouvé(s)
              </div>
            </div>
          </div>

          {/* Payments Table */}
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
                      Méthode
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
                  {filteredPayments.map((payment) => (
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
                        <div className="flex items-center space-x-2">
                          {getPaymentMethodIcon(payment.type_paiement)}
                          <span className="text-sm text-gray-900 capitalize">
                            {payment.type_paiement}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {payment.assure ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Assuré ({payment.taux_remboursement}%)
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
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="text-blue-600 hover:text-blue-900">
                            <Edit className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {filteredPayments.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun paiement trouvé pour les critères sélectionnés</p>
            </div>
          )}
        </div>
      )}

      {/* Unpaid Tab */}
      {activeTab === 'unpaid' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Consultations non payées</h3>
              <p className="text-sm text-gray-600 mt-1">
                Liste des visites terminées qui n'ont pas encore été payées
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
                      Patient
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
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
                  {unpaidAppointments.map((appointment) => (
                    <tr key={appointment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {new Date(appointment.date).toLocaleDateString('fr-FR')}
                          </div>
                          <div className="text-sm text-gray-500">
                            {appointment.heure}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {appointment.patient?.prenom} {appointment.patient?.nom}
                          </div>
                          <div className="text-sm text-gray-500">
                            {appointment.motif}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <Phone className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-900">
                            {appointment.patient?.telephone || 'N/A'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          appointment.statut === 'termine' 
                            ? 'bg-green-100 text-green-800'
                            : appointment.statut === 'absent'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {appointment.statut === 'termine' ? 'Terminé' :
                           appointment.statut === 'absent' ? 'Absent' : 'En retard'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleMarkAsPaid(appointment)}
                            className="text-green-600 hover:text-green-900 px-3 py-1 bg-green-100 rounded-lg"
                          >
                            Marquer payé
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {unpaidAppointments.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-green-600 font-medium">Excellente nouvelle !</p>
              <p className="text-gray-500">Tous les paiements sont à jour</p>
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
                    {selectedPayment.assure ? 
                      `Assuré (${selectedPayment.taux_remboursement}%)` : 
                      'Non assuré'
                    }
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
    </div>
  );
};

export default Billing;