import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  Calendar, 
  Search, 
  Download, 
  TrendingUp,
  Users,
  FileText,
  Filter
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Billing = ({ user }) => {
  const [payments, setPayments] = useState([]);
  const [filteredPayments, setFilteredPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [monthFilter, setMonthFilter] = useState('');
  const [stats, setStats] = useState({
    total_jour: 0,
    total_mois: 0,
    total_annee: 0,
    nb_visites: 0,
    nb_controles: 0,
    nb_assures: 0
  });

  useEffect(() => {
    fetchPayments();
    calculateStats();
  }, []);

  useEffect(() => {
    filterPayments();
  }, [payments, searchTerm, dateFilter, monthFilter]);

  const fetchPayments = async () => {
    try {
      const response = await axios.get('/api/payments');
      setPayments(response.data);
    } catch (error) {
      console.error('Error fetching payments:', error);
      toast.error('Erreur lors du chargement des paiements');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = async () => {
    try {
      const today = new Date();
      const currentMonth = today.getMonth() + 1;
      const currentYear = today.getFullYear();
      const todayStr = today.toISOString().split('T')[0];

      // Simuler des statistiques
      setStats({
        total_jour: 900,
        total_mois: 25000,
        total_annee: 280000,
        nb_visites: 45,
        nb_controles: 23,
        nb_assures: 38
      });
    } catch (error) {
      console.error('Error calculating stats:', error);
    }
  };

  const filterPayments = () => {
    let filtered = [...payments];

    if (searchTerm) {
      // Cette fonctionnalité nécessiterait de récupérer les informations patient
      filtered = filtered.filter(payment => 
        payment.patient_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (dateFilter) {
      filtered = filtered.filter(payment => payment.date === dateFilter);
    }

    if (monthFilter) {
      filtered = filtered.filter(payment => 
        payment.date.startsWith(monthFilter)
      );
    }

    setFilteredPayments(filtered);
  };

  const exportToExcel = () => {
    // Simulation d'export Excel
    toast.success('Export Excel en cours...');
    
    // Créer un CSV simple
    const csvContent = [
      ['Date', 'Patient', 'Montant', 'Type', 'Statut'],
      ...filteredPayments.map(payment => [
        payment.date,
        payment.patient_id,
        payment.montant,
        payment.type_paiement,
        payment.statut
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `facturation_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
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
          <h1 className="text-2xl font-bold text-gray-900">Facturation</h1>
          <p className="text-gray-600">Rapports et statistiques financières</p>
        </div>
        <button
          onClick={exportToExcel}
          className="btn-primary flex items-center space-x-2"
        >
          <Download className="w-5 h-5" />
          <span>Export Excel</span>
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          icon={DollarSign}
          title="Recette du jour"
          value={`${stats.total_jour} TND`}
          color="text-green-600"
          subtitle="Paiements encaissés aujourd'hui"
        />
        <StatCard
          icon={Calendar}
          title="Recette du mois"
          value={`${stats.total_mois} DH`}
          color="text-blue-600"
          subtitle="Total mensuel"
        />
        <StatCard
          icon={TrendingUp}
          title="Recette annuelle"
          value={`${stats.total_annee} DH`}
          color="text-purple-600"
          subtitle="Total annuel"
        />
      </div>

      {/* Second Row Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={FileText}
          title="Visites payantes"
          value={stats.nb_visites}
          color="text-orange-600"
          subtitle="Ce mois-ci"
        />
        <StatCard
          icon={Users}
          title="Contrôles gratuits"
          value={stats.nb_controles}
          color="text-teal-600"
          subtitle="Ce mois-ci"
        />
        <StatCard
          icon={Users}
          title="Patients assurés"
          value={stats.nb_assures}
          color="text-indigo-600"
          subtitle="Ce mois-ci"
        />
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recherche patient
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Nom du patient..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date spécifique
            </label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="input-field"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mois
            </label>
            <input
              type="month"
              value={monthFilter}
              onChange={(e) => setMonthFilter(e.target.value)}
              className="input-field"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setDateFilter('');
                setMonthFilter('');
              }}
              className="btn-outline w-full flex items-center justify-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Réinitialiser</span>
            </button>
          </div>
        </div>
      </div>

      {/* Payments Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Historique des paiements
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {filteredPayments.length} paiement(s) trouvé(s)
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
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
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statut
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredPayments.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>Aucun paiement trouvé</p>
                  </td>
                </tr>
              ) : (
                filteredPayments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(payment.date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {payment.patient_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {payment.montant} DH
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className="capitalize">{payment.type_paiement}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        payment.statut === 'paye' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {payment.statut === 'paye' ? 'Payé' : 'Non payé'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Monthly Charts Placeholder */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Évolution mensuelle
        </h3>
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Graphique des recettes mensuelles</p>
            <p className="text-sm text-gray-400 mt-2">
              Fonctionnalité disponible prochainement
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Billing;