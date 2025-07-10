import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Calendar, 
  Clock, 
  CheckCircle, 
  DollarSign, 
  TrendingUp,
  MessageCircle,
  Phone,
  AlertCircle
} from 'lucide-react';
import axios from 'axios';

const Dashboard = ({ user }) => {
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
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'info',
      titre: 'Rappel vaccination',
      message: 'Lina Alami - Rappel vaccin à 18 mois',
      time: '10:30',
      urgent: false
    },
    {
      id: 2,
      type: 'urgent',
      titre: 'Patient en retard',
      message: 'RDV 09:00 - Yassine Ben Ahmed non arrivé',
      time: '09:15',
      urgent: true
    }
  ]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/api/dashboard');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
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

  const MessageCard = ({ message }) => (
    <div className={`p-4 rounded-lg border-l-4 ${message.urgent ? 'bg-red-50 border-red-400' : 'bg-blue-50 border-blue-400'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {message.urgent ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : (
            <MessageCircle className="w-4 h-4 text-blue-500" />
          )}
          <span className="font-medium text-gray-900">{message.titre}</span>
        </div>
        <span className="text-xs text-gray-500">{message.time}</span>
      </div>
      <p className="mt-1 text-sm text-gray-700">{message.message}</p>
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
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Bonjour {user.name} 👋
        </h1>
        <p className="text-primary-100">
          Voici un aperçu de votre journée
        </p>
      </div>

      {/* Stats Grid - Optimized for PC */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
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
          value={`${stats.recette_jour} DH`}
          color="text-purple-600"
          subtitle="Paiements encaissés"
        />
      </div>

      {/* Messages and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Messages */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Messages & Rappels</h3>
            <span className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">
              {messages.filter(m => m.urgent).length} urgent
            </span>
          </div>
          <div className="space-y-3">
            {messages.map((message) => (
              <MessageCard key={message.id} message={message} />
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between p-3 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors">
              <div className="flex items-center space-x-3">
                <Users className="w-5 h-5 text-primary-600" />
                <span className="font-medium text-primary-900">Ajouter un patient</span>
              </div>
              <div className="text-primary-600">→</div>
            </button>
            
            <button className="w-full flex items-center justify-between p-3 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors">
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-secondary-600" />
                <span className="font-medium text-secondary-900">Nouveau RDV</span>
              </div>
              <div className="text-secondary-600">→</div>
            </button>
            
            <button className="w-full flex items-center justify-between p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
              <div className="flex items-center space-x-3">
                <Phone className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-900">Rappels téléphoniques</span>
              </div>
              <div className="text-green-600">→</div>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Activité Récente</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">Consultation terminée - Omar Tazi (14:30)</span>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-700">Paiement encaissé - 300 DH (14:35)</span>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <span className="text-sm text-gray-700">Patient en attente - Yassine Ben Ahmed (Salle 1)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;