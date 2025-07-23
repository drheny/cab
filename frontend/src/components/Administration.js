import React, { useState, useEffect, useRef } from 'react';
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
  FileText,
  Edit2,
  Save,
  X,
  Key,
  Lock,
  UserCheck,
  Monitor,
  HardDrive,
  Gauge,
  TrendingUp,
  PieChart,
  Clock,
  Play,
  Pause,
  Square,
  Minimize2,
  Maximize2,
  Weight,
  Ruler,
  Brain,
  Edit3,
  TrendingDown
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
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

const Administration = ({ user }) => {
  const [activeTab, setActiveTab] = useState('statistiques');
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

  // User Management States
  const [allUsers, setAllUsers] = useState([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'secretaire',
    password: ''
  });
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [editingPermissions, setEditingPermissions] = useState(null);
  const [systemInfo, setSystemInfo] = useState({
    version: '2.0',
    uptime: '0 jours',
    storage: { used: 0, total: 100 },
    performance: { responseTime: 0, errors: 0 },
    lastBackup: null
  });

  // Charts data
  const [chartsData, setChartsData] = useState(null);
  const [chartsLoading, setChartsLoading] = useState(false);

  // Reports data
  const [reportData, setReportData] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportForm, setReportForm] = useState({
    reportType: 'single', // 'single' or 'multi'
    singleMonth: new Date().getMonth() + 1,
    singleYear: new Date().getFullYear(),
    startMonth: new Date().getMonth() + 1,
    startYear: new Date().getFullYear(),
    endMonth: new Date().getMonth() + 1,
    endYear: new Date().getFullYear()
  });

  // Advanced Reports States
  const [advancedReportData, setAdvancedReportData] = useState(null);
  const [advancedReportLoading, setAdvancedReportLoading] = useState(false);
  const [advancedReportType, setAdvancedReportType] = useState('monthly');
  const [advancedReportPeriod, setAdvancedReportPeriod] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    semester: 1,
    startDate: '',
    endDate: ''
  });
  const [selectedMetrics, setSelectedMetrics] = useState({
    overview: true,
    financial: true,
    patients: true,
    operations: true,
    predictions: true
  });
  const [activeReportTab, setActiveReportTab] = useState('overview');
  const [demographicsData, setDemographicsData] = useState(null);
  const [topPatientsData, setTopPatientsData] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    if (user?.permissions?.administration) {
      fetchAdminStats();
      if (user?.permissions?.manage_users) {
        fetchUsers();
      }
      fetchSystemInfo();
      fetchChartsData();
    }
  }, [user]);

  // Check if user has administration access
  const hasAdminAccess = user?.permissions?.administration || user?.role === 'medecin';
  
  if (!hasAdminAccess) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="flex items-center space-x-3 text-red-600">
          <AlertTriangle className="w-6 h-6" />
          <div>
            <h3 className="font-medium">Accès refusé</h3>
            <p className="text-sm text-gray-600">Vous n'avez pas les permissions pour accéder à cette page.</p>
          </div>
        </div>
      </div>
    );
  }

  // User Management Functions
  const fetchChartsData = async () => {
    try {
      setChartsLoading(true);
      const response = await axios.get('/api/admin/charts/yearly-evolution');
      setChartsData(response.data);
    } catch (error) {
      console.error('Error fetching charts data:', error);
      toast.error('Erreur lors du chargement des graphiques');
    } finally {
      setChartsLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/api/admin/users');
      setAllUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Erreur lors du chargement des utilisateurs');
    }
  };

  const fetchSystemInfo = async () => {
    try {
      // Mock system info - in production, this would come from an API
      setSystemInfo({
        version: '2.0',
        uptime: Math.floor(Date.now() / (1000 * 60 * 60 * 24)) + ' jours',
        storage: { used: 45, total: 100 },
        performance: { responseTime: 125, errors: 2 },
        lastBackup: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error fetching system info:', error);
    }
  };

  const handleCreateUser = async () => {
    try {
      if (!userForm.username || !userForm.full_name || !userForm.password) {
        toast.error('Veuillez remplir tous les champs obligatoires');
        return;
      }

      await axios.post('/api/admin/users', userForm);
      toast.success('Utilisateur créé avec succès');
      setShowUserModal(false);
      setUserForm({ username: '', email: '', full_name: '', role: 'secretaire', password: '' });
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la création de l\'utilisateur');
    }
  };

  const handleUpdateUser = async () => {
    try {
      if (!editingUser) return;

      const updateData = { ...userForm };
      if (!updateData.password) {
        delete updateData.password; // Don't update password if empty
      }

      await axios.put(`/api/admin/users/${editingUser.id}`, updateData);
      toast.success('Utilisateur mis à jour avec succès');
      setShowUserModal(false);
      setEditingUser(null);
      setUserForm({ username: '', email: '', full_name: '', role: 'secretaire', password: '' });
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${username}" ?\n\nCette action est irréversible.`)) {
      return;
    }

    try {
      await axios.delete(`/api/admin/users/${userId}`);
      toast.success('Utilisateur supprimé avec succès');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleUpdatePassword = async () => {
    try {
      if (!passwordForm.newPassword || !passwordForm.confirmPassword) {
        toast.error('Veuillez saisir le nouveau mot de passe');
        return;
      }

      if (passwordForm.newPassword !== passwordForm.confirmPassword) {
        toast.error('Les mots de passe ne correspondent pas');
        return;
      }

      await axios.put(`/api/admin/users/${user.id}`, {
        password: passwordForm.newPassword
      });

      toast.success('Mot de passe mis à jour avec succès');
      setShowPasswordModal(false);
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      console.error('Error updating password:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour du mot de passe');
    }
  };

  const handleUpdatePermissions = async (userId, permissions) => {
    try {
      await axios.put(`/api/admin/users/${userId}/permissions`, permissions);
      toast.success('Permissions mises à jour avec succès');
      setEditingPermissions(null);
      fetchUsers();
    } catch (error) {
      console.error('Error updating permissions:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour des permissions');
    }
  };

  const openEditUser = (user) => {
    setEditingUser(user);
    setUserForm({
      username: user.username,
      email: user.email || '',
      full_name: user.full_name,
      role: user.role,
      password: '' // Don't prefill password
    });
    setShowUserModal(true);
  };

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

  const generateAdvancedReport = async () => {
    try {
      setReportLoading(true);
      
      let url = '/api/admin/monthly-report';
      const params = new URLSearchParams();
      
      if (reportForm.reportType === 'single') {
        params.append('year', reportForm.singleYear);
        params.append('month', reportForm.singleMonth);
      } else {
        params.append('start_month', reportForm.startMonth);
        params.append('start_year', reportForm.startYear);
        params.append('end_month', reportForm.endMonth);
        params.append('end_year', reportForm.endYear);
      }
      
      const response = await axios.get(`${url}?${params}`);
      const report = response.data;
      setReportData(report);
      
      // Create enhanced CSV content
      let csvContent = [];
      
      if (report.type === 'multi_month') {
        // Multi-month report CSV
        csvContent = [
          ['Rapport Multi-Mois', report.periode],
          ['Période', `Du ${report.start_date} au ${report.end_date}`],
          ['Nombre de mois', report.num_months],
          [''],
          ['=== TOTAUX ==='],
          ['Nouveaux patients', report.totals.nouveaux_patients],
          ['Total consultations', report.totals.consultations_totales],
          ['Nombre de visites', report.totals.nb_visites],
          ['Nombre de contrôles', report.totals.nb_controles],
          ['Patients assurés', report.totals.nb_assures],
          ['Recette totale (TND)', report.totals.recette_totale],
          ['Relances téléphoniques', report.totals.nb_relances_telephoniques],
          [''],
          ['=== MOYENNES MENSUELLES ==='],
          ['Nouveaux patients/mois', report.averages.nouveaux_patients],
          ['Consultations/mois', report.averages.consultations_totales],
          ['Visites/mois', report.averages.nb_visites],
          ['Contrôles/mois', report.averages.nb_controles],
          ['Recette/mois (TND)', report.averages.recette_totale],
          [''],
          ['=== DÉTAIL PAR MOIS ==='],
          ['Mois', 'Nouveaux Patients', 'Consultations', 'Visites', 'Contrôles', 'Assurés', 'Recette (TND)', 'Relances']
        ];
        
        // Add monthly details
        report.monthly_reports.forEach(monthData => {
          csvContent.push([
            monthData.periode,
            monthData.nouveaux_patients,
            monthData.consultations_totales,
            monthData.nb_visites,
            monthData.nb_controles,
            monthData.nb_assures,
            monthData.recette_totale,
            monthData.nb_relances_telephoniques
          ]);
        });
        
      } else {
        // Single month report CSV (existing logic)
        csvContent = [
          ['Rapport Mensuel', report.periode],
          [''],
          ['Indicateur', 'Valeur'],
          ['Nouveaux patients', report.nouveaux_patients],
          ['Total consultations', report.consultations_totales],
          ['Nombre de visites', report.nb_visites],
          ['Nombre de contrôles', report.nb_controles],
          ['Patients assurés', report.nb_assures],
          ['Recette totale (TND)', report.recette_totale],
          ['Relances téléphoniques', report.nb_relances_telephoniques]
        ];
      }
      
      csvContent.push([''], ['Généré le', new Date(report.generated_at).toLocaleString('fr-FR')]);
      
      const csvString = csvContent.map(row => row.join(',')).join('\n');
      
      // Download CSV
      const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `rapport_${report.type === 'multi_month' ? 'multi_mois' : 'mensuel'}_${report.periode.replace(/[\/\-\s]/g, '-')}.csv`;
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`Rapport généré avec succès`);
    } catch (error) {
      console.error('Error generating advanced report:', error);
      toast.error('Erreur lors de la génération du rapport');
    } finally {
      setReportLoading(false);
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
      a.download = `rapport_mensuel_${reportData.periode.replace('/', '-')}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Rapport ${reportData.periode} généré avec succès`);
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
      
      // Use the new admin export endpoint
      const response = await axios.get(`/api/admin/export/${dataType}`);
      const { data, count, collection } = response.data;
      
      if (count === 0) {
        toast.error('Aucune donnée à exporter');
        return;
      }
      
      // Generate filename
      const filename = `sauvegarde_${collection}_${new Date().toISOString().split('T')[0]}.csv`;
      
      // Convert to CSV with UTF-8 BOM for Excel compatibility
      const headers = Object.keys(data[0]).join(',');
      const csvRows = data.map(row => 
        Object.values(row).map(value => {
          // Handle commas and quotes in data
          const stringValue = String(value || '');
          return stringValue.includes(',') || stringValue.includes('"') 
            ? `"${stringValue.replace(/"/g, '""')}"` 
            : stringValue;
        }).join(',')
      );
      
      const csvContent = [headers, ...csvRows].join('\n');
      
      // Add UTF-8 BOM for Excel compatibility
      const BOM = '\uFEFF';
      const csvWithBOM = BOM + csvContent;
      
      // Download
      const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Sauvegarde ${collection} terminée (${count} éléments)`);
    } catch (error) {
      console.error(`Error exporting ${dataType}:`, error);
      toast.error(`Erreur lors de la sauvegarde ${dataType}: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ========== ADVANCED REPORTS FUNCTIONS ==========
  
  const generateNewAdvancedReport = async () => {
    try {
      setAdvancedReportLoading(true);
      const period = advancedReportPeriod;
      
      let params = new URLSearchParams({
        period_type: advancedReportType
      });
      
      // Add period-specific parameters
      if (advancedReportType === 'monthly') {
        params.append('year', period.year);
        params.append('month', period.month);
      } else if (advancedReportType === 'semester') {
        params.append('year', period.year);
        params.append('semester', period.semester);
      } else if (advancedReportType === 'annual') {
        params.append('year', period.year);
      } else if (advancedReportType === 'custom') {
        params.append('start_date', period.startDate);
        params.append('end_date', period.endDate);
      }
      
      const response = await axios.get(`/api/admin/advanced-reports?${params}`);
      const reportData = response.data;
      
      setAdvancedReportData(reportData);
      setAlerts(reportData.alerts || []);
      
      toast.success('Rapport avancé généré avec succès');
    } catch (error) {
      console.error('Error generating advanced report:', error);
      toast.error('Erreur lors de la génération du rapport avancé');
    } finally {
      setAdvancedReportLoading(false);
    }
  };

  const fetchDemographicsData = async () => {
    try {
      const today = new Date();
      const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
      
      const params = new URLSearchParams({
        start_date: oneYearAgo.toISOString().split('T')[0],
        end_date: today.toISOString().split('T')[0]
      });
      
      const response = await axios.get(`/api/admin/reports/demographics?${params}`);
      setDemographicsData(response.data);
    } catch (error) {
      console.error('Error fetching demographics:', error);
    }
  };

  const fetchTopPatientsData = async (metric = 'revenue', limit = 10) => {
    try {
      const params = new URLSearchParams({
        metric,
        limit: limit.toString(),
        period_months: '12'
      });
      
      const response = await axios.get(`/api/admin/reports/top-patients?${params}`);
      setTopPatientsData(response.data);
    } catch (error) {
      console.error('Error fetching top patients:', error);
    }
  };

  const exportAdvancedReportToExcel = () => {
    if (!advancedReportData) {
      toast.error('Aucun rapport à exporter');
      return;
    }

    try {
      const data = advancedReportData;
      const stats = data.advanced_statistics;
      
      // Create comprehensive Excel-style CSV
      let csvContent = [
        ['=== RAPPORT AVANCÉ ==='],
        ['Période', data.metadata.periode],
        ['Type', data.metadata.type],
        ['Généré le', new Date(data.metadata.generated_at).toLocaleString('fr-FR')],
        [''],
        ['=== SYNTHÈSE EXÉCUTIVE ==='],
        ['Total Consultations', stats.consultations.total],
        ['Visites', `${stats.consultations.visites.count} (${stats.consultations.visites.percentage}%)`],
        ['Contrôles', `${stats.consultations.controles.count} (${stats.consultations.controles.percentage}%)`],
        ['Revenus Visites (TND)', stats.consultations.visites.revenue],
        ['Temps Attente Moyen (min)', stats.durees.attente_moyenne],
        ['Temps Consultation Moyen (min)', stats.durees.consultation_moyenne],
        ['Patients Inactifs', `${stats.patients_inactifs.count} (${stats.patients_inactifs.percentage}%)`],
        ['Taux de Fidélisation (%)', stats.fidelisation.taux_retour],
        [''],
        ['=== TOP 10 PATIENTS RENTABLES ==='],
        ['Nom', 'Consultations', 'Revenus (TND)', 'Dernière Visite']
      ];

      // Add top patients
      stats.top_patients.forEach(patient => {
        csvContent.push([
          patient.name,
          patient.consultations,
          patient.revenue,
          patient.last_visit
        ]);
      });

      csvContent.push(['']);
      csvContent.push(['=== UTILISATION DES SALLES ===']);
      csvContent.push(['Salle 1', `${stats.salles.salle1.utilisation}%`, `${stats.salles.salle1.consultations} consultations`]);
      csvContent.push(['Salle 2', `${stats.salles.salle2.utilisation}%`, `${stats.salles.salle2.consultations} consultations`]);
      
      // Add alerts if any
      if (data.alerts && data.alerts.length > 0) {
        csvContent.push(['']);
        csvContent.push(['=== ALERTES ===']);
        data.alerts.forEach(alert => {
          csvContent.push([alert.type, alert.message, `Seuil: ${alert.threshold}`]);
        });
      }

      // Convert to CSV string
      const csvString = csvContent.map(row => row.join(',')).join('\n');
      
      // Download
      const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_avance_${data.metadata.type}_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('Rapport exporté avec succès');
    } catch (error) {
      console.error('Error exporting advanced report:', error);
      toast.error('Erreur lors de l\'export');
    }
  };

  const renderChart = (chartData, chartOptions) => {
    // Simple chart component - to be implemented later
    return (
      <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Graphique à implémenter</p>
      </div>
    );
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

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'statistiques', label: 'Statistiques', icon: BarChart3 },
            { id: 'donnees', label: 'Gestion Données', icon: Database },
            { id: 'utilisateurs', label: 'Gestion Utilisateurs', icon: Users, requiresPermission: 'manage_users' },
            { id: 'acces', label: 'Gestion Accès', icon: Key },
            { id: 'droits', label: 'Gestion Droits', icon: Shield, requiresPermission: 'manage_users' },
            { id: 'systeme', label: 'Info Système', icon: Monitor }
          ].filter(tab => !tab.requiresPermission || user?.permissions?.[tab.requiresPermission]).map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'statistiques' && (
        <div className="space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard
              icon={Users}
              title="Total Patients"
              value={stats.total_patients}
              color="text-blue-600"
              subtitle="Patients enregistrés"
            />
            <StatCard
              icon={UserPlus}
              title="Nouveaux cette année"
              value={stats.nouveaux_patients_annee}
              color="text-green-600"
              subtitle="Nouveaux patients"
            />
            <StatCard
              icon={Activity}
              title="Patients Inactifs"
              value={stats.patients_inactifs}
              color="text-orange-600"
              subtitle=">12 mois sans consultation"
            />
          </div>

          {/* Charts Section */}
          {chartsData && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-2 mb-6">
                <TrendingUp className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Évolution Annuelle {chartsData.year}</h2>
                <button
                  onClick={fetchChartsData}
                  disabled={chartsLoading}
                  className="ml-auto flex items-center space-x-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
                >
                  <RefreshCw className={`w-4 h-4 ${chartsLoading ? 'animate-spin' : ''}`} />
                  <span>Actualiser</span>
                </button>
              </div>

              {chartsLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              ) : (
                <div className="space-y-8">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <DollarSign className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">Recette Annuelle</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-600">{chartsData.totals.recette_annee} TND</p>
                    </div>
                    
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <UserPlus className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-green-900">Nouveaux Patients</span>
                      </div>
                      <p className="text-2xl font-bold text-green-600">{chartsData.totals.nouveaux_patients_annee}</p>
                    </div>
                    
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <Activity className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-900">Consultations</span>
                      </div>
                      <p className="text-2xl font-bold text-purple-600">{chartsData.totals.consultations_annee}</p>
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
                            labels: chartsData.monthly_data.map(d => d.month_short),
                            datasets: [
                              {
                                label: 'Recette (TND)',
                                data: chartsData.monthly_data.map(d => d.recette_mensuelle),
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
                            labels: chartsData.monthly_data.map(d => d.month_short),
                            datasets: [
                              {
                                label: 'Nouveaux Patients',
                                data: chartsData.monthly_data.map(d => d.nouveaux_patients),
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
                            labels: chartsData.monthly_data.map(d => d.month_short),
                            datasets: [
                              {
                                label: 'Visites',
                                data: chartsData.monthly_data.map(d => d.nb_visites),
                                borderColor: 'rgb(147, 51, 234)',
                                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                                tension: 0.1
                              },
                              {
                                label: 'Contrôles',
                                data: chartsData.monthly_data.map(d => d.nb_controles),
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
                            labels: chartsData.monthly_data.map(d => d.month_short),
                            datasets: [
                              {
                                label: 'Total Consultations',
                                data: chartsData.monthly_data.map(d => d.consultations_totales),
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
              )}
            </div>
          )}

          {/* Advanced Reports Section - New Implementation */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Rapports Avancés</h2>
              </div>
              
              {/* Alerts Display */}
              {alerts.length > 0 && (
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className="text-sm font-medium text-red-600">{alerts.length} alerte(s)</span>
                </div>
              )}
            </div>

            {/* Alerts Panel */}
            {alerts.length > 0 && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="text-sm font-medium text-red-800 mb-2">🚨 Alertes Détectées</h3>
                <div className="space-y-2">
                  {alerts.map((alert, index) => (
                    <div key={index} className="flex items-center space-x-2 text-sm text-red-700">
                      <span className="font-medium">{alert.type}:</span>
                      <span>{alert.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Period Configuration */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">📅 Sélection de Période</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Type de période</label>
                  <select
                    value={advancedReportType}
                    onChange={(e) => setAdvancedReportType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="monthly">📅 Mensuel</option>
                    <option value="semester">📊 Semestriel</option>
                    <option value="annual">📈 Annuel</option>
                    <option value="custom">🎛️ Personnalisé</option>
                  </select>
                </div>

                {advancedReportType === 'monthly' && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Mois</label>
                      <select
                        value={advancedReportPeriod.month}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, month: parseInt(e.target.value) }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      >
                        {Array.from({ length: 12 }, (_, i) => (
                          <option key={i + 1} value={i + 1}>
                            {new Date(2023, i, 1).toLocaleDateString('fr-FR', { month: 'long' })}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                      <select
                        value={advancedReportPeriod.year}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, year: parseInt(e.target.value) }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      >
                        {Array.from({ length: 5 }, (_, i) => (
                          <option key={2025 - i} value={2025 - i}>
                            {2025 - i}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {advancedReportType === 'semester' && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Semestre</label>
                      <select
                        value={advancedReportPeriod.semester}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, semester: parseInt(e.target.value) }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      >
                        <option value={1}>1er Semestre</option>
                        <option value={2}>2e Semestre</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                      <select
                        value={advancedReportPeriod.year}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, year: parseInt(e.target.value) }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      >
                        {Array.from({ length: 5 }, (_, i) => (
                          <option key={2025 - i} value={2025 - i}>
                            {2025 - i}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {advancedReportType === 'annual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                    <select
                      value={advancedReportPeriod.year}
                      onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, year: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {Array.from({ length: 5 }, (_, i) => (
                        <option key={2025 - i} value={2025 - i}>
                          Année {2025 - i}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {advancedReportType === 'custom' && (
                  <div className="space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date de début</label>
                      <input
                        type="date"
                        value={advancedReportPeriod.startDate}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, startDate: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date de fin</label>
                      <input
                        type="date"
                        value={advancedReportPeriod.endDate}
                        onChange={(e) => setAdvancedReportPeriod(prev => ({ ...prev, endDate: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                <button
                  onClick={generateNewAdvancedReport}
                  disabled={advancedReportLoading}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium"
                >
                  {advancedReportLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Génération...</span>
                    </>
                  ) : (
                    <>
                      <BarChart3 className="w-4 h-4" />
                      <span>Générer le Rapport</span>
                    </>
                  )}
                </button>
              </div>

              {/* Metrics Selection */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">📊 Métriques Incluses</h3>
                <div className="space-y-2">
                  {Object.entries(selectedMetrics).map(([key, value]) => (
                    <label key={key} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={(e) => setSelectedMetrics(prev => ({ ...prev, [key]: e.target.checked }))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        {key === 'overview' && '🏠 Vue d\'ensemble'}
                        {key === 'financial' && '💰 Financier'}
                        {key === 'patients' && '👥 Patients'}
                        {key === 'operations' && '⚙️ Opérations'}
                        {key === 'predictions' && '🔮 Prédictions'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">⚡ Actions Rapides</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => fetchDemographicsData()}
                    className="w-full text-left px-3 py-2 text-sm bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 border border-purple-200"
                  >
                    👥 Analyse Démographique
                  </button>
                  <button
                    onClick={() => fetchTopPatientsData('revenue')}
                    className="w-full text-left px-3 py-2 text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100 border border-green-200"
                  >
                    💎 Top Patients (Revenus)
                  </button>
                  <button
                    onClick={() => fetchTopPatientsData('frequency')}
                    className="w-full text-left px-3 py-2 text-sm bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 border border-orange-200"
                  >
                    🔄 Top Patients (Fréquence)
                  </button>
                  {advancedReportData && (
                    <button
                      onClick={exportAdvancedReportToExcel}
                      className="w-full text-left px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 border border-blue-200"
                    >
                      📄 Export Excel
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Report Display */}
            {advancedReportData && (
              <div className="space-y-6">
                {/* Report Tabs */}
                <div className="border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8">
                    {[
                      { id: 'overview', label: '🏠 Vue d\'ensemble', icon: BarChart3 },
                      { id: 'financial', label: '💰 Financier', icon: DollarSign },
                      { id: 'patients', label: '👥 Patients', icon: Users },
                      { id: 'operations', label: '⚙️ Opérations', icon: Activity },
                      { id: 'predictions', label: '🔮 Prédictions', icon: TrendingUp }
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveReportTab(tab.id)}
                        className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                          activeReportTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </nav>
                </div>

                {/* Tab Content */}
                {activeReportTab === 'overview' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <Calendar className="w-5 h-5 text-blue-600" />
                        <span className="font-medium text-blue-900">Total Consultations</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-600">
                        {advancedReportData.advanced_statistics.consultations.total}
                      </p>
                    </div>

                    <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <DollarSign className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-green-900">Revenus Visites</span>
                      </div>
                      <p className="text-2xl font-bold text-green-600">
                        {advancedReportData.advanced_statistics.consultations.visites.revenue} TND
                      </p>
                    </div>

                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <Clock className="w-5 h-5 text-orange-600" />
                        <span className="font-medium text-orange-900">Temps Attente Moyen</span>
                      </div>
                      <p className="text-2xl font-bold text-orange-600">
                        {advancedReportData.advanced_statistics.durees.attente_moyenne} min
                      </p>
                    </div>

                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                        <span className="font-medium text-purple-900">Taux Fidélisation</span>
                      </div>
                      <p className="text-2xl font-bold text-purple-600">
                        {advancedReportData.advanced_statistics.fidelisation.taux_retour}%
                      </p>
                    </div>
                  </div>
                )}

                {activeReportTab === 'financial' && (
                  <div className="space-y-6">
                    {/* Répartition Visite/Contrôle */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-4">💰 Répartition Visite/Contrôle</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white p-4 rounded-lg border">
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Visites</p>
                            <p className="text-2xl font-bold text-green-600">
                              {advancedReportData.advanced_statistics.consultations.visites.count}
                            </p>
                            <p className="text-sm text-green-600">
                              {advancedReportData.advanced_statistics.consultations.visites.percentage}%
                            </p>
                            <p className="text-lg font-semibold text-green-700 mt-2">
                              {advancedReportData.advanced_statistics.consultations.visites.revenue} TND
                            </p>
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg border">
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Contrôles</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {advancedReportData.advanced_statistics.consultations.controles.count}
                            </p>
                            <p className="text-sm text-blue-600">
                              {advancedReportData.advanced_statistics.consultations.controles.percentage}%
                            </p>
                            <p className="text-lg font-semibold text-blue-700 mt-2">Gratuit</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Top 10 Patients Rentables */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-4">💎 Top 10 Patients Rentables</h4>
                      <div className="overflow-x-auto">
                        <table className="min-w-full bg-white rounded-lg overflow-hidden">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Nom</th>
                              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Consultations</th>
                              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Revenus (TND)</th>
                              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Dernière Visite</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {advancedReportData.advanced_statistics.top_patients.map((patient, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                <td className="px-4 py-2 text-sm text-gray-900">{patient.name}</td>
                                <td className="px-4 py-2 text-sm text-gray-600">{patient.consultations}</td>
                                <td className="px-4 py-2 text-sm font-semibold text-green-600">{patient.revenue}</td>
                                <td className="px-4 py-2 text-sm text-gray-600">{patient.last_visit}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {activeReportTab === 'patients' && (
                  <div className="space-y-6">
                    {/* Demographics */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-4">👶 Répartition par Âge</h4>
                        <div className="space-y-2">
                          {Object.entries(advancedReportData.advanced_statistics.demographics.age_groups).map(([ageGroup, count]) => (
                            <div key={ageGroup} className="flex justify-between items-center bg-white p-2 rounded">
                              <span className="text-sm text-gray-700">{ageGroup} ans</span>
                              <span className="font-semibold text-blue-600">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-4">🏘️ Répartition par Adresse</h4>
                        <div className="space-y-2">
                          {Object.entries(advancedReportData.advanced_statistics.demographics.addresses).map(([address, count]) => (
                            <div key={address} className="flex justify-between items-center bg-white p-2 rounded">
                              <span className="text-sm text-gray-700">{address}</span>
                              <span className="font-semibold text-purple-600">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Patients Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                        <h5 className="font-medium text-red-900 mb-2">😴 Patients Inactifs</h5>
                        <p className="text-2xl font-bold text-red-600">
                          {advancedReportData.advanced_statistics.patients_inactifs.count}
                        </p>
                        <p className="text-sm text-red-600">
                          {advancedReportData.advanced_statistics.patients_inactifs.percentage}% des patients
                        </p>
                      </div>

                      <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                        <h5 className="font-medium text-green-900 mb-2">🆕 Nouveaux Patients</h5>
                        <p className="text-2xl font-bold text-green-600">
                          {advancedReportData.advanced_statistics.fidelisation.nouveaux_patients}
                        </p>
                      </div>

                      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-2">🔄 Patients Récurrents</h5>
                        <p className="text-2xl font-bold text-blue-600">
                          {advancedReportData.advanced_statistics.fidelisation.patients_recurrents}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {activeReportTab === 'operations' && (
                  <div className="space-y-6">
                    {/* Durées */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                        <h5 className="font-medium text-orange-900 mb-2">⏱️ Temps d'Attente</h5>
                        <p className="text-2xl font-bold text-orange-600">
                          {advancedReportData.advanced_statistics.durees.attente_moyenne} min
                        </p>
                        <p className="text-sm text-orange-600">
                          Max: {advancedReportData.advanced_statistics.durees.attente_max} min
                        </p>
                      </div>

                      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-2">🩺 Durée Consultation</h5>
                        <p className="text-2xl font-bold text-blue-600">
                          {advancedReportData.advanced_statistics.durees.consultation_moyenne} min
                        </p>
                        <p className="text-sm text-blue-600">
                          Max: {advancedReportData.advanced_statistics.durees.consultation_max} min
                        </p>
                      </div>
                    </div>

                    {/* Utilisation des Salles */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-4">🏥 Utilisation des Salles</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white p-4 rounded-lg border">
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Salle 1</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {advancedReportData.advanced_statistics.salles.salle1.utilisation}%
                            </p>
                            <p className="text-sm text-blue-600">
                              {advancedReportData.advanced_statistics.salles.salle1.consultations} consultations
                            </p>
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg border">
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Salle 2</p>
                            <p className="text-2xl font-bold text-green-600">
                              {advancedReportData.advanced_statistics.salles.salle2.utilisation}%
                            </p>
                            <p className="text-sm text-green-600">
                              {advancedReportData.advanced_statistics.salles.salle2.consultations} consultations
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Relances Téléphoniques */}
                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                      <h4 className="font-medium text-purple-900 mb-4">📞 Relances Téléphoniques</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                          <p className="text-sm text-purple-600">Total</p>
                          <p className="text-xl font-bold text-purple-600">
                            {advancedReportData.advanced_statistics.relances.total}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-purple-600">Traitées</p>
                          <p className="text-xl font-bold text-green-600">
                            {advancedReportData.advanced_statistics.relances.traitees}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-purple-600">Taux de Réponse</p>
                          <p className="text-xl font-bold text-purple-600">
                            {advancedReportData.advanced_statistics.relances.taux_reponse}%
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeReportTab === 'predictions' && advancedReportData.predictions && (
                  <div className="space-y-6">
                    {/* Prédictions */}
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                      <h4 className="font-medium text-gray-900 mb-4 flex items-center">
                        <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                        🔮 Prédictions du Mois Prochain
                      </h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white p-4 rounded-lg text-center">
                          <p className="text-sm text-gray-600">Consultations Estimées</p>
                          <p className="text-2xl font-bold text-blue-600">
                            {advancedReportData.predictions.next_month.consultations_estimees}
                          </p>
                        </div>
                        <div className="bg-white p-4 rounded-lg text-center">
                          <p className="text-sm text-gray-600">Revenus Estimés</p>
                          <p className="text-2xl font-bold text-green-600">
                            {advancedReportData.predictions.next_month.revenue_estime} TND
                          </p>
                        </div>
                        <div className="bg-white p-4 rounded-lg text-center">
                          <p className="text-sm text-gray-600">Niveau de Confiance</p>
                          <p className="text-2xl font-bold text-purple-600">
                            {advancedReportData.predictions.next_month.confiance}%
                          </p>
                        </div>
                      </div>
                      
                      {advancedReportData.predictions.trend && (
                        <div className="mt-4 text-center">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            advancedReportData.predictions.trend === 'croissant' 
                              ? 'bg-green-100 text-green-800' 
                              : advancedReportData.predictions.trend === 'décroissant'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {advancedReportData.predictions.trend === 'croissant' && '📈'}
                            {advancedReportData.predictions.trend === 'décroissant' && '📉'}
                            {advancedReportData.predictions.trend === 'stable' && '📊'}
                            Tendance: {advancedReportData.predictions.trend}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Saisonnalité */}
                    {advancedReportData.seasonality && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-4">🗓️ Patterns Saisonniers</h4>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Pics */}
                          <div>
                            <h5 className="font-medium text-green-700 mb-3">📈 Pics d'Activité</h5>
                            <div className="space-y-2">
                              {advancedReportData.seasonality.pics.map((pic, index) => (
                                <div key={index} className="bg-green-50 p-3 rounded border border-green-200">
                                  <div className="flex justify-between items-center">
                                    <span className="font-medium text-green-900">{pic.periode}</span>
                                    <span className="text-green-600 font-semibold">{pic.evolution}</span>
                                  </div>
                                  <p className="text-sm text-green-700 mt-1">{pic.raison}</p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Creux */}
                          <div>
                            <h5 className="font-medium text-red-700 mb-3">📉 Creux d'Activité</h5>
                            <div className="space-y-2">
                              {advancedReportData.seasonality.creux.map((creux, index) => (
                                <div key={index} className="bg-red-50 p-3 rounded border border-red-200">
                                  <div className="flex justify-between items-center">
                                    <span className="font-medium text-red-900">{creux.periode}</span>
                                    <span className="text-red-600 font-semibold">{creux.evolution}</span>
                                  </div>
                                  <p className="text-sm text-red-700 mt-1">{creux.raison}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Comparaison Année N vs N-1 */}
                    {advancedReportData.comparison && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-4">📊 Comparaison Annuelle (N vs N-1)</h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-center">
                              <p className="text-sm text-gray-600">Consultations</p>
                              <p className="text-lg font-bold text-gray-900">
                                {advancedReportData.comparison.consultations.current}
                              </p>
                              <p className="text-sm text-gray-500">
                                vs {advancedReportData.comparison.consultations.previous}
                              </p>
                              <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${
                                advancedReportData.comparison.consultations.evolution.startsWith('+')
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {advancedReportData.comparison.consultations.evolution}
                              </span>
                            </div>
                          </div>

                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-center">
                              <p className="text-sm text-gray-600">Revenus (TND)</p>
                              <p className="text-lg font-bold text-gray-900">
                                {advancedReportData.comparison.revenue.current}
                              </p>
                              <p className="text-sm text-gray-500">
                                vs {advancedReportData.comparison.revenue.previous}
                              </p>
                              <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${
                                advancedReportData.comparison.revenue.evolution.startsWith('+')
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {advancedReportData.comparison.revenue.evolution}
                              </span>
                            </div>
                          </div>

                          <div className="bg-white p-4 rounded-lg border">
                            <div className="text-center">
                              <p className="text-sm text-gray-600">Visites</p>
                              <p className="text-lg font-bold text-gray-900">
                                {advancedReportData.comparison.visites.current}
                              </p>
                              <p className="text-sm text-gray-500">
                                vs {advancedReportData.comparison.visites.previous}
                              </p>
                              <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${
                                advancedReportData.comparison.visites.evolution.startsWith('+')
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {advancedReportData.comparison.visites.evolution}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {!advancedReportData && !advancedReportLoading && (
              <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg mb-2">Aucun rapport généré</p>
                <p className="text-gray-400 text-sm">
                  Configurez les paramètres ci-dessus et cliquez sur "Générer le Rapport" pour commencer
                </p>
              </div>
            )}
          </div>

          {/* Actions rapides */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <RefreshCw className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Actions Rapides</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <button
                onClick={fetchInactivePatients}
                disabled={loading}
                className="flex flex-col items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors border border-orange-200"
              >
                <Activity className="w-8 h-8 text-orange-600 mb-2" />
                <span className="text-sm font-medium text-orange-900">Patients inactifs</span>
                <span className="text-xs text-orange-600 mt-1">Voir la liste</span>
              </button>

              <button
                onClick={generateAdvancedReport}
                disabled={reportLoading}
                className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors border border-blue-200"
              >
                <FileText className="w-8 h-8 text-blue-600 mb-2" />
                <span className="text-sm font-medium text-blue-900">Rapport avancé</span>
                <span className="text-xs text-blue-600 mt-1">Multi-mois + Stats</span>
              </button>

              <button
                onClick={() => performMaintenance('update_calculated_fields')}
                disabled={loading}
                className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors border border-green-200"
              >
                <RefreshCw className="w-8 h-8 text-green-600 mb-2" />
                <span className="text-sm font-medium text-green-900">Mise à jour</span>
                <span className="text-xs text-green-600 mt-1">Champs calculés</span>
              </button>

              <button
                onClick={() => performMaintenance('verify_data_integrity')}
                disabled={loading}
                className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors border border-purple-200"
              >
                <ClipboardCheck className="w-8 h-8 text-purple-600 mb-2" />
                <span className="text-sm font-medium text-purple-900">Vérification</span>
                <span className="text-xs text-purple-600 mt-1">Intégrité</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'donnees' && (
        <div className="space-y-6">
          {/* Data Management */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <Database className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Gestion des Données</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Data Export */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Sauvegarde des données</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => exportData('patients')}
                    disabled={loading}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
                  >
                    <Download className="w-4 h-4" />
                    <span>Sauvegarder patients</span>
                  </button>
                  
                  <button
                    onClick={() => exportData('consultations')}
                    disabled={loading}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    <span>Sauvegarder consultations</span>
                  </button>
                  
                  <button
                    onClick={() => exportData('payments')}
                    disabled={loading}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg disabled:opacity-50"
                  >
                    <DollarSign className="w-4 h-4" />
                    <span>Sauvegarder paiements</span>
                  </button>
                </div>
              </div>

              {/* Data Reset */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Réinitialisation</h3>
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-800">Zone dangereuse</span>
                  </div>
                  <p className="text-xs text-red-600 mb-3">
                    La réinitialisation supprime définitivement les données sélectionnées.
                  </p>
                  <button
                    onClick={() => setShowResetModal(true)}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Réinitialiser base</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'utilisateurs' && user?.permissions?.manage_users && (
        <div className="space-y-6">
          {/* User Management */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Gestion des Utilisateurs</h2>
              </div>
              <button
                onClick={() => {
                  setEditingUser(null);
                  setUserForm({ username: '', email: '', full_name: '', role: 'secretaire', password: '' });
                  setShowUserModal(true);
                }}
                className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
              >
                <Plus className="w-4 h-4" />
                <span>Nouvel utilisateur</span>
              </button>
            </div>

            {/* Users List */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilisateur</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rôle</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {allUsers.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                          <div className="text-sm text-gray-500">{user.username}</div>
                          {user.email && <div className="text-xs text-gray-400">{user.email}</div>}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.role === 'medecin' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {user.role === 'medecin' ? 'Médecin' : 'Secrétaire'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Actif' : 'Inactif'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => openEditUser(user)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Modifier"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          
                          <button
                            onClick={() => setEditingPermissions(user)}
                            className="text-green-600 hover:text-green-900"
                            title="Permissions"
                          >
                            <Shield className="w-4 h-4" />
                          </button>
                          
                          {user.id !== user.id && (
                            <button
                              onClick={() => handleDeleteUser(user.id, user.username)}
                              className="text-red-600 hover:text-red-900"
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'acces' && (
        <div className="space-y-6">
          {/* Access Management */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <Key className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Gestion des Accès</h2>
            </div>

            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Mon mot de passe</h3>
                <p className="text-sm text-blue-700 mb-4">Modifier votre mot de passe de connexion</p>
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  <Lock className="w-4 h-4" />
                  <span>Changer le mot de passe</span>
                </button>
              </div>

              {user?.permissions?.manage_users && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-900 mb-2">Comptes par défaut</h3>
                  <p className="text-sm text-yellow-700 mb-4">
                    Médecin: medecin / medecin123<br />
                    Secrétaire: secretaire / secretaire123
                  </p>
                  <p className="text-xs text-yellow-600">
                    ⚠️ Changez ces mots de passe par défaut pour sécuriser le système
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'droits' && user?.permissions?.manage_users && (
        <div className="space-y-6">
          {/* Rights Management */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <Shield className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Gestion des Droits</h2>
            </div>

            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-medium text-green-900 mb-2">Droits par défaut</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-green-700">
                  <div>
                    <h4 className="font-medium mb-2">Médecin (Accès complet)</h4>
                    <ul className="space-y-1">
                      <li>• Toutes les pages</li>
                      <li>• Gestion des utilisateurs</li>
                      <li>• Export/Réinitialisation</li>
                      <li>• Administration</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Secrétaire (Accès limité)</h4>
                    <ul className="space-y-1">
                      <li>• Dashboard, Patients, Calendrier</li>
                      <li>• Messages, Facturation</li>
                      <li>• Consultation (lecture seule)</li>
                      <li>• Pas d'administration</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Permissions personnalisables</h3>
                <p className="text-sm text-blue-700 mb-4">
                  Cliquez sur l'icône permissions (🛡️) dans la liste des utilisateurs pour personnaliser les droits de chaque secrétaire.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-blue-600">
                  <div>
                    <h5 className="font-medium">Pages</h5>
                    <ul>
                      <li>• Dashboard</li>
                      <li>• Patients</li>
                      <li>• Calendrier</li>
                      <li>• Messages</li>
                      <li>• Facturation</li>
                      <li>• Consultation</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium">Actions</h5>
                    <ul>
                      <li>• Créer RDV</li>
                      <li>• Modifier RDV</li>
                      <li>• Voir paiements</li>
                      <li>• Modifier paiements</li>
                      <li>• Export données</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium">Restrictions</h5>
                    <ul>
                      <li>• Consultation lecture seule</li>
                      <li>• Pas de suppression</li>
                      <li>• Pas d'administration</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'systeme' && (
        <div className="space-y-6">
          {/* System Information */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-6">
              <Monitor className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Informations Système</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Settings className="w-4 h-4 text-gray-600" />
                  <h3 className="font-medium text-gray-900">Version</h3>
                </div>
                <p className="text-2xl font-bold text-gray-900">{systemInfo.version}</p>
                <p className="text-xs text-gray-500">Cabinet Médical</p>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="w-4 h-4 text-green-600" />
                  <h3 className="font-medium text-gray-900">Uptime</h3>
                </div>
                <p className="text-2xl font-bold text-green-600">{systemInfo.uptime}</p>
                <p className="text-xs text-gray-500">Temps de fonctionnement</p>
              </div>

              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <HardDrive className="w-4 h-4 text-blue-600" />
                  <h3 className="font-medium text-gray-900">Stockage</h3>
                </div>
                <p className="text-2xl font-bold text-blue-600">{systemInfo.storage.used}%</p>
                <p className="text-xs text-gray-500">Espace utilisé</p>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Gauge className="w-4 h-4 text-purple-600" />
                  <h3 className="font-medium text-gray-900">Performance</h3>
                </div>
                <p className="text-2xl font-bold text-purple-600">{systemInfo.performance.responseTime}ms</p>
                <p className="text-xs text-gray-500">Temps de réponse</p>
              </div>
            </div>

            <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-medium text-yellow-900 mb-2">Dernière sauvegarde</h3>
              <p className="text-sm text-yellow-700">
                {systemInfo.lastBackup 
                  ? new Date(systemInfo.lastBackup).toLocaleString('fr-FR')
                  : 'Aucune sauvegarde effectuée'
                }
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                Effectuez régulièrement des sauvegardes via l'onglet "Gestion Données"
              </p>
            </div>
          </div>
        </div>
      )}

      {/* User Create/Edit Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingUser ? 'Modifier utilisateur' : 'Nouvel utilisateur'}
              </h3>
              <button
                onClick={() => setShowUserModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom d'utilisateur *</label>
                <input
                  type="text"
                  value={userForm.username}
                  onChange={(e) => setUserForm(prev => ({ ...prev, username: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="nom_utilisateur"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet *</label>
                <input
                  type="text"
                  value={userForm.full_name}
                  onChange={(e) => setUserForm(prev => ({ ...prev, full_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Prénom Nom"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="email@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rôle</label>
                <select
                  value={userForm.role}
                  onChange={(e) => setUserForm(prev => ({ ...prev, role: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="secretaire">Secrétaire</option>
                  <option value="medecin">Médecin</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mot de passe {editingUser ? '(laisser vide pour ne pas modifier)' : '*'}
                </label>
                <input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm(prev => ({ ...prev, password: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowUserModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={editingUser ? handleUpdateUser : handleCreateUser}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
              >
                {editingUser ? 'Modifier' : 'Créer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Changer le mot de passe</h3>
              <button
                onClick={() => setShowPasswordModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nouveau mot de passe</label>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm(prev => ({ ...prev, newPassword: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmer le mot de passe</label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowPasswordModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={handleUpdatePassword}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
              >
                Modifier
              </button>
            </div>
          </div>
        </div>
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
                <X className="w-5 h-5" />
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
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={handleResetDatabase}
                disabled={loading}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
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
                  <X className="w-5 h-5" />
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
                          <button 
                            className="text-left hover:text-blue-600"
                            onClick={() => {
                              // Navigate to patient details
                              window.location.href = `/patients?patient=${patient.id}`;
                            }}
                          >
                            <div className="text-sm font-medium text-gray-900 hover:text-blue-600">
                              {patient.prenom} {patient.nom}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {patient.id}
                            </div>
                          </button>
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