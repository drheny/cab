import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Phone, 
  Calendar, 
  User,
  MessageCircle
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const PatientsList = ({ user }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    date_naissance: '',
    sexe: 'M',
    telephone: '',
    adresse: '',
    nom_parent: '',
    telephone_parent: '',
    assurance: '',
    numero_assurance: '',
    allergies: '',
    antecedents: ''
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get('/api/patients');
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
      toast.error('Erreur lors du chargement des patients');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredPatients = patients.filter(patient => 
    patient.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.nom_parent.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.telephone.includes(searchTerm)
  );

  const handleCreatePatient = async () => {
    try {
      await axios.post('/api/patients', formData);
      toast.success('Patient créé avec succès');
      setShowModal(false);
      resetForm();
      fetchPatients();
    } catch (error) {
      console.error('Error creating patient:', error);
      toast.error('Erreur lors de la création du patient');
    }
  };

  const handleUpdatePatient = async () => {
    try {
      await axios.put(`/api/patients/${selectedPatient.id}`, formData);
      toast.success('Patient mis à jour avec succès');
      setShowModal(false);
      resetForm();
      fetchPatients();
    } catch (error) {
      console.error('Error updating patient:', error);
      toast.error('Erreur lors de la mise à jour du patient');
    }
  };

  const handleDeletePatient = async (patientId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce patient ?')) {
      try {
        await axios.delete(`/api/patients/${patientId}`);
        toast.success('Patient supprimé avec succès');
        fetchPatients();
      } catch (error) {
        console.error('Error deleting patient:', error);
        toast.error('Erreur lors de la suppression du patient');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      nom: '',
      prenom: '',
      date_naissance: '',
      sexe: 'M',
      telephone: '',
      adresse: '',
      nom_parent: '',
      telephone_parent: '',
      assurance: '',
      numero_assurance: '',
      allergies: '',
      antecedents: ''
    });
    setSelectedPatient(null);
  };

  const openModal = (patient = null) => {
    if (patient) {
      setSelectedPatient(patient);
      setFormData(patient);
    } else {
      resetForm();
    }
    setShowModal(true);
  };

  const getWhatsAppLink = (phone) => {
    const cleanPhone = phone.replace(/\D/g, '');
    return `https://wa.me/212${cleanPhone.startsWith('0') ? cleanPhone.substring(1) : cleanPhone}`;
  };

  const calculateAge = (birthDate) => {
    const today = new Date();
    const birth = new Date(birthDate);
    const age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      return age - 1;
    }
    return age;
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
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-gray-600">Gestion des fiches patients</p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Nouveau Patient</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Rechercher un patient..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Patients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPatients.map((patient) => (
          <div key={patient.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="bg-primary-100 p-2 rounded-full">
                  <User className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {patient.prenom} {patient.nom}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {calculateAge(patient.date_naissance)} ans • {patient.sexe === 'M' ? 'Garçon' : 'Fille'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => openModal(patient)}
                  className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeletePatient(patient.id)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center space-x-2 text-sm">
                <User className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">Parent: {patient.nom_parent}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Phone className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">{patient.telephone_parent}</span>
              </div>
              {patient.assurance && (
                <div className="flex items-center space-x-2 text-sm">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{patient.assurance}</span>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <a
                href={getWhatsAppLink(patient.telephone_parent)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                <MessageCircle className="w-4 h-4" />
                <span>WhatsApp</span>
              </a>
              <button className="flex-1 bg-primary-500 hover:bg-primary-600 text-white text-sm py-2 px-3 rounded-lg flex items-center justify-center space-x-2 transition-colors">
                <Calendar className="w-4 h-4" />
                <span>RDV</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                {selectedPatient ? 'Modifier le patient' : 'Nouveau patient'}
              </h2>

              <form onSubmit={(e) => {
                e.preventDefault();
                selectedPatient ? handleUpdatePatient() : handleCreatePatient();
              }}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                    <input
                      type="text"
                      value={formData.nom}
                      onChange={(e) => setFormData({...formData, nom: e.target.value})}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                    <input
                      type="text"
                      value={formData.prenom}
                      onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date de naissance</label>
                    <input
                      type="date"
                      value={formData.date_naissance}
                      onChange={(e) => setFormData({...formData, date_naissance: e.target.value})}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Sexe</label>
                    <select
                      value={formData.sexe}
                      onChange={(e) => setFormData({...formData, sexe: e.target.value})}
                      className="input-field"
                    >
                      <option value="M">Masculin</option>
                      <option value="F">Féminin</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                    <input
                      type="tel"
                      value={formData.telephone}
                      onChange={(e) => setFormData({...formData, telephone: e.target.value})}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nom du parent</label>
                    <input
                      type="text"
                      value={formData.nom_parent}
                      onChange={(e) => setFormData({...formData, nom_parent: e.target.value})}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone du parent</label>
                    <input
                      type="tel"
                      value={formData.telephone_parent}
                      onChange={(e) => setFormData({...formData, telephone_parent: e.target.value})}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Assurance</label>
                    <input
                      type="text"
                      value={formData.assurance}
                      onChange={(e) => setFormData({...formData, assurance: e.target.value})}
                      className="input-field"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
                    <input
                      type="text"
                      value={formData.adresse}
                      onChange={(e) => setFormData({...formData, adresse: e.target.value})}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Allergies</label>
                    <textarea
                      value={formData.allergies}
                      onChange={(e) => setFormData({...formData, allergies: e.target.value})}
                      className="input-field"
                      rows="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Antécédents</label>
                    <textarea
                      value={formData.antecedents}
                      onChange={(e) => setFormData({...formData, antecedents: e.target.value})}
                      className="input-field"
                      rows="2"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="btn-outline"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    {selectedPatient ? 'Modifier' : 'Créer'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientsList;