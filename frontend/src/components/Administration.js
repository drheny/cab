import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Users, 
  BarChart3, 
  Database, 
  Download,
  Upload,
  Trash2,
  Plus,
  Shield,
  Activity,
  FileSpreadsheet,
  Eye,
  MessageSquare,
  Phone,
  Wrench,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Calendar,
  DollarSign,
  UserPlus,
  ClipboardCheck,
  FileText
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Administration = ({ user }) => {
  const [stats, setStats] = useState({
    total_patients: 0,
    nouveaux_patients_annee: 0,
    patients_inactifs: 0
  });
  const [loading, setLoading] = useState(false);
  const [inactivePatients, setInactivePatients] = useState([]);
  const [showInactivePatients, setShowInactivePatients] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetOptions, setResetOptions] = useState({
    patients: false,
    appointments: false, 
    consultations: false,
    facturation: false
  });
  const [maintenanceResults, setMaintenanceResults] = useState({});

  useEffect(() => {
    if (user.type === 'medecin') {
      fetchAdminStats();
    }
  }, [user.type]);

  const fetchAdminStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/admin/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching admin stats:', error);
      toast.error('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };

  const fetchInactivePatients = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/admin/inactive-patients');
      setInactivePatients(response.data.inactive_patients);
      setShowInactivePatients(true);
    } catch (error) {
      console.error('Error fetching inactive patients:', error);
      toast.error('Erreur lors du chargement des patients inactifs');
    } finally {
      setLoading(false);
    }
  };

  const handleResetDatabase = async () => {
    const selectedCollections = Object.keys(resetOptions).filter(key => resetOptions[key]);
    
    if (selectedCollections.length === 0) {
      toast.error('Veuillez sélectionner au moins une collection à réinitialiser');
      return;
    }

    const confirmText = `Êtes-vous sûr de vouloir réinitialiser: ${selectedCollections.join(', ')} ?\n\nCette action est IRRÉVERSIBLE !`;
    
    if (!window.confirm(confirmText)) return;

    try {
      setLoading(true);
      
      for (const collection of selectedCollections) {
        await axios.delete(`/api/admin/database/${collection}`);
      }
      
      toast.success(`Collections réinitialisées: ${selectedCollections.join(', ')}`);
      setShowResetModal(false);
      setResetOptions({ patients: false, appointments: false, consultations: false, facturation: false });
      
      // Refresh stats after reset
      await fetchAdminStats();
      
    } catch (error) {
      console.error('Error resetting database:', error);
      toast.error('Erreur lors de la réinitialisation');
    } finally {
      setLoading(false);
    }
  };

  const generateMonthlyReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/admin/monthly-report');
      const reportData = response.data;
      
      // Create CSV content
      const csvContent = [
        ['Rapport Mensuel', reportData.periode],
        [''],
        ['Indicateur', 'Valeur'],
        ['Nouveaux patients', reportData.nouveaux_patients],
        ['Total consultations', reportData.consultations_totales],
        ['Nombre de visites', reportData.nb_visites],
        ['Nombre de contrôles', reportData.nb_controles],
        ['Patients assurés', reportData.nb_assures],
        ['Recette totale (TND)', reportData.recette_totale],
        ['Relances téléphoniques', reportData.nb_relances_telephoniques],
        [''],
        ['Généré le', new Date(reportData.generated_at).toLocaleString('fr-FR')]
      ].map(row => row.join(',')).join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_mensuel_${reportData.periode.replace('/', '_')}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('Rapport mensuel généré et téléchargé');
    } catch (error) {
      console.error('Error generating monthly report:', error);
      toast.error('Erreur lors de la génération du rapport');
    } finally {
      setLoading(false);
    }
  };

  const performMaintenance = async (action) => {
    try {
      setLoading(true);
      const response = await axios.post(`/api/admin/maintenance/${action}`);
      const result = response.data;
      
      setMaintenanceResults(prev => ({
        ...prev,
        [action]: result
      }));
      
      toast.success(result.message);
    } catch (error) {
      console.error(`Error performing maintenance ${action}:`, error);
      toast.error(`Erreur lors de la maintenance: ${action}`);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (dataType) => {
    try {
      setLoading(true);
      let data = [];
      let filename = '';
      
      switch (dataType) {
        case 'patients':
          const patientsResponse = await axios.get('/api/patients');
          data = patientsResponse.data;
          filename = 'base_patients.csv';
          break;
        case 'consultations':
          const consultationsResponse = await axios.get('/api/consultations');
          data = consultationsResponse.data;
          filename = 'base_consultations.csv';
          break;
        case 'payments':
          const paymentsResponse = await axios.get('/api/payments');
          data = paymentsResponse.data;
          filename = 'base_paiements.csv';
          break;
      }
      
      if (data.length === 0) {
        toast.error('Aucune donnée à exporter');
        return;
      }
      
      // Convert to CSV
      const headers = Object.keys(data[0]).join(',');
      const csvContent = [headers, ...data.map(row => Object.values(row).join(','))].join('\n');
      
      // Download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Export ${dataType} terminé`);
    } catch (error) {
      console.error(`Error exporting ${dataType}:`, error);
      toast.error(`Erreur lors de l'export ${dataType}`);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>
            {loading ? '...' : value}
          </p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
        <p className="text-gray-600">Gestion système et statistiques avancées</p>
      </div>

      {/* Access Control */}
      {user.type !== 'medecin' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-red-500" />
            <span className="text-red-700 font-medium">Accès restreint</span>
          </div>
          <p className="text-red-600 text-sm mt-1">
            Seuls les médecins ont accès à la section administration.
          </p>
        </div>
      )}

      {user.type === 'medecin' && (
        <>
          {/* Statistics Cards - Only the 3 required */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard
              icon={Users}
              title="Total Patients"
              value={stats.total_patients}
              color="text-blue-600"
              subtitle="Patients dans la base"
            />
            <StatCard
              icon={UserPlus}
              title="Nouveaux cette année"
              value={stats.nouveaux_patients_annee}
              color="text-green-600"
              subtitle="Depuis janvier"
            />
            <StatCard
              icon={Activity}
              title="Patients inactifs"
              value={stats.patients_inactifs}
              color="text-orange-600"
              subtitle="+12 mois sans consultation"
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Section Gestion de Données */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Gestion de Données
              </h3>
              
              <div className="space-y-4">
                {/* Réinitialisation base de données */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <Trash2 className="w-4 h-4 mr-2 text-red-500" />
                    Réinitialiser la base de données
                  </h4>
                  <button
                    onClick={() => setShowResetModal(true)}
                    className="w-full btn-outline border-red-200 text-red-700 hover:bg-red-50"
                  >
                    Configurer la réinitialisation
                  </button>
                </div>

                {/* Exports */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <Download className="w-4 h-4 mr-2 text-blue-500" />
                    Sauvegarde et Export Excel
                  </h4>
                  <div className="grid grid-cols-1 gap-2">
                    <button
                      onClick={() => exportData('patients')}
                      disabled={loading}
                      className="btn-outline flex items-center justify-center space-x-2"
                    >
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Base Patients</span>
                    </button>
                    <button
                      onClick={() => exportData('consultations')}
                      disabled={loading}
                      className="btn-outline flex items-center justify-center space-x-2"
                    >
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Base Consultations</span>
                    </button>
                    <button
                      onClick={() => exportData('payments')}
                      disabled={loading}
                      className="btn-outline flex items-center justify-center space-x-2"
                    >
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Base Paiements</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Section Gestion Utilisateurs */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Gestion Utilisateurs
              </h3>
              
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">Dr Heni Dridi</h4>
                      <p className="text-sm text-gray-500">Médecin - Accès complet</p>
                    </div>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      Actif
                    </span>
                  </div>
                  <button className="btn-outline w-full">
                    Modifier code d'accès
                  </button>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">Secrétaire</h4>
                      <p className="text-sm text-gray-500">Secrétaire - Accès restreint</p>
                    </div>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      Actif
                    </span>
                  </div>
                  <button className="btn-outline w-full">
                    Modifier droits d'accès
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Actions Rapides */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              Actions Rapides
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Rapport mensuel */}
              <button 
                onClick={generateMonthlyReport}
                disabled={loading}
                className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg text-left transition-colors"
              >
                <BarChart3 className="w-6 h-6 text-blue-600 mb-2" />
                <h4 className="font-medium text-gray-900">Rapport mensuel</h4>
                <p className="text-sm text-gray-600">PDF + Excel avec toutes les stats</p>
              </button>
              
              {/* Patients inactifs */}
              <button 
                onClick={fetchInactivePatients}
                disabled={loading}
                className="p-4 bg-orange-50 hover:bg-orange-100 rounded-lg text-left transition-colors"
              >
                <Users className="w-6 h-6 text-orange-600 mb-2" />
                <h4 className="font-medium text-gray-900">Patients inactifs</h4>
                <p className="text-sm text-gray-600">Liste + actions de contact</p>
              </button>
              
              {/* Maintenance - Nettoyage messages */}
              <button 
                onClick={() => performMaintenance('cleanup_messages')}
                disabled={loading}
                className="p-4 bg-purple-50 hover:bg-purple-100 rounded-lg text-left transition-colors"
              >
                <MessageSquare className="w-6 h-6 text-purple-600 mb-2" />
                <h4 className="font-medium text-gray-900">Nettoyer messages</h4>
                <p className="text-sm text-gray-600">Supprimer anciens messages</p>
              </button>
              
              {/* Maintenance - Vérification intégrité */}
              <button 
                onClick={() => performMaintenance('verify_data_integrity')}
                disabled={loading}
                className="p-4 bg-green-50 hover:bg-green-100 rounded-lg text-left transition-colors"
              >
                <CheckCircle className="w-6 h-6 text-green-600 mb-2" />
                <h4 className="font-medium text-gray-900">Vérifier intégrité</h4>
                <p className="text-sm text-gray-600">Contrôler cohérence données</p>
              </button>
              
              {/* Maintenance - Mise à jour champs */}
              <button 
                onClick={() => performMaintenance('update_calculated_fields')}
                disabled={loading}
                className="p-4 bg-indigo-50 hover:bg-indigo-100 rounded-lg text-left transition-colors"
              >
                <RefreshCw className="w-6 h-6 text-indigo-600 mb-2" />
                <h4 className="font-medium text-gray-900">MàJ champs calculés</h4>
                <p className="text-sm text-gray-600">Âge, liens WhatsApp</p>
              </button>
              
              {/* Maintenance - Optimisation */}
              <button 
                onClick={() => performMaintenance('optimize_database')}
                disabled={loading}
                className="p-4 bg-teal-50 hover:bg-teal-100 rounded-lg text-left transition-colors"
              >
                <Activity className="w-6 h-6 text-teal-600 mb-2" />
                <h4 className="font-medium text-gray-900">Optimiser BDD</h4>
                <p className="text-sm text-gray-600">Performance et stockage</p>
              </button>
            </div>
          </div>

          {/* Results of maintenance actions */}
          {Object.keys(maintenanceResults).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Résultats Maintenance</h3>
              <div className="space-y-3">
                {Object.entries(maintenanceResults).map(([action, result]) => (
                  <div key={action} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900 capitalize">{action.replace('_', ' ')}</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        result.completed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {result.completed ? 'Terminé' : 'Erreur'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{result.message}</p>
                    {result.details && (
                      <div className="text-xs text-gray-500 mt-2">
                        {JSON.stringify(result.details, null, 2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Reset Database Modal */}
      {showResetModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Réinitialisation Base de Données</h3>
              <button
                onClick={() => setShowResetModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-red-600 text-sm mb-4">
                ⚠️ Attention: Cette action est IRRÉVERSIBLE
              </p>
              
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={resetOptions.patients}
                    onChange={(e) => setResetOptions(prev => ({...prev, patients: e.target.checked}))}
                    className="mr-2"
                  />
                  <span className="text-sm">Patients</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={resetOptions.appointments}
                    onChange={(e) => setResetOptions(prev => ({...prev, appointments: e.target.checked}))}
                    className="mr-2"
                  />
                  <span className="text-sm">Rendez-vous</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={resetOptions.consultations}
                    onChange={(e) => setResetOptions(prev => ({...prev, consultations: e.target.checked}))}
                    className="mr-2"
                  />
                  <span className="text-sm">Consultations</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={resetOptions.facturation}
                    onChange={(e) => setResetOptions(prev => ({...prev, facturation: e.target.checked}))}
                    className="mr-2"
                  />
                  <span className="text-sm">Facturation (Paiements + Caisse)</span>
                </label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowResetModal(false)}
                className="btn-outline"
              >
                Annuler
              </button>
              <button
                onClick={handleResetDatabase}
                disabled={loading}
                className="btn-primary bg-red-600 hover:bg-red-700"
              >
                {loading ? 'Réinitialisation...' : 'Confirmer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inactive Patients Modal */}
      {showInactivePatients && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Patients Inactifs ({inactivePatients.length})
                </h3>
                <button
                  onClick={() => setShowInactivePatients(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Âge</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dernière consultation</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inactivePatients.map((patient) => (
                      <tr key={patient.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {patient.prenom} {patient.nom}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {patient.id}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {patient.age}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {patient.last_consultation_date ? 
                            new Date(patient.last_consultation_date).toLocaleDateString('fr-FR') : 
                            'Aucune'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-2">
                            <button 
                              className="text-blue-600 hover:text-blue-900"
                              title="Consulter fiche"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            
                            {patient.lien_whatsapp && (
                              <a 
                                href={patient.lien_whatsapp}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-green-600 hover:text-green-900"
                                title="Contacter WhatsApp"
                              >
                                <MessageSquare className="w-4 h-4" />
                              </a>
                            )}
                            
                            <button 
                              className="text-red-600 hover:text-red-900"
                              title="Supprimer patient"
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
          </div>
        </div>
      )}
    </div>
  );
};

export default Administration;