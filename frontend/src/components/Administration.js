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
  Activity
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Administration = ({ user }) => {
  const [stats, setStats] = useState({
    total_patients: 0,
    nouveaux_patients_mois: 0,
    patients_inactifs: 0,
    consultations_mois: 0,
    rdv_annules: 0,
    taux_presence: 0
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAdminStats();
  }, []);

  const fetchAdminStats = async () => {
    try {
      // Simuler des statistiques d'administration
      setStats({
        total_patients: 247,
        nouveaux_patients_mois: 18,
        patients_inactifs: 32,
        consultations_mois: 156,
        rdv_annules: 8,
        taux_presence: 92
      });
    } catch (error) {
      console.error('Error fetching admin stats:', error);
    }
  };

  const exportDatabase = async () => {
    setLoading(true);
    try {
      // Simuler l'export de la base de données
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Créer un fichier de données simulé
      const data = {
        export_date: new Date().toISOString(),
        patients: await axios.get('/api/patients').then(res => res.data),
        appointments: await axios.get('/api/appointments').then(res => res.data),
        consultations: await axios.get('/api/consultations').then(res => res.data),
        payments: await axios.get('/api/payments').then(res => res.data)
      };

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cabinet_medical_backup_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('Base de données exportée avec succès');
    } catch (error) {
      console.error('Error exporting database:', error);
      toast.error('Erreur lors de l\'export');
    } finally {
      setLoading(false);
    }
  };

  const initDemoData = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir réinitialiser les données de démonstration ?')) {
      try {
        await axios.get('/api/init-demo');
        toast.success('Données de démonstration réinitialisées');
        fetchAdminStats();
      } catch (error) {
        console.error('Error initializing demo data:', error);
        toast.error('Erreur lors de la réinitialisation');
      }
    }
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
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard
              icon={Users}
              title="Total Patients"
              value={stats.total_patients}
              color="text-blue-600"
              subtitle="Patients enregistrés"
            />
            <StatCard
              icon={Plus}
              title="Nouveaux ce mois"
              value={stats.nouveaux_patients_mois}
              color="text-green-600"
              subtitle="Nouveaux patients"
            />
            <StatCard
              icon={Activity}
              title="Patients inactifs"
              value={stats.patients_inactifs}
              color="text-orange-600"
              subtitle="+6 mois sans consultation"
            />
            <StatCard
              icon={BarChart3}
              title="Consultations"
              value={stats.consultations_mois}
              color="text-purple-600"
              subtitle="Ce mois-ci"
            />
            <StatCard
              icon={Trash2}
              title="RDV annulés"
              value={stats.rdv_annules}
              color="text-red-600"
              subtitle="Ce mois-ci"
            />
            <StatCard
              icon={Settings}
              title="Taux de présence"
              value={`${stats.taux_presence}%`}
              color="text-teal-600"
              subtitle="Moyenne mensuelle"
            />
          </div>

          {/* System Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Database Management */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Gestion des données
              </h3>
              <div className="space-y-4">
                <button
                  onClick={exportDatabase}
                  disabled={loading}
                  className="w-full btn-primary flex items-center justify-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>{loading ? 'Export en cours...' : 'Exporter la base de données'}</span>
                </button>
                
                <button
                  onClick={initDemoData}
                  className="w-full btn-secondary flex items-center justify-center space-x-2"
                >
                  <Database className="w-4 h-4" />
                  <span>Réinitialiser données démo</span>
                </button>
              </div>
            </div>

            {/* User Management */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Gestion des utilisateurs
              </h3>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Dr. Médecin</h4>
                      <p className="text-sm text-gray-500">Accès complet</p>
                    </div>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      Actif
                    </span>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Secrétaire</h4>
                      <p className="text-sm text-gray-500">Accès restreint</p>
                    </div>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      Actif
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* System Information */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Informations système
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Application</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Version:</span>
                    <span className="font-medium">1.0.0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Base de données:</span>
                    <span className="font-medium">MongoDB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Dernier backup:</span>
                    <span className="font-medium">
                      {new Date().toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Performance</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Temps de réponse:</span>
                    <span className="font-medium text-green-600">Excellent</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Disponibilité:</span>
                    <span className="font-medium text-green-600">99.9%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Stockage utilisé:</span>
                    <span className="font-medium">2.1 GB</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Actions rapides
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg text-left transition-colors">
                <BarChart3 className="w-6 h-6 text-blue-600 mb-2" />
                <h4 className="font-medium text-gray-900">Rapport mensuel</h4>
                <p className="text-sm text-gray-600">Générer le rapport du mois</p>
              </button>
              
              <button className="p-4 bg-green-50 hover:bg-green-100 rounded-lg text-left transition-colors">
                <Users className="w-6 h-6 text-green-600 mb-2" />
                <h4 className="font-medium text-gray-900">Patients inactifs</h4>
                <p className="text-sm text-gray-600">Identifier les patients à relancer</p>
              </button>
              
              <button className="p-4 bg-purple-50 hover:bg-purple-100 rounded-lg text-left transition-colors">
                <Settings className="w-6 h-6 text-purple-600 mb-2" />
                <h4 className="font-medium text-gray-900">Maintenance</h4>
                <p className="text-sm text-gray-600">Nettoyer et optimiser</p>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Administration;