import React, { useState, useEffect } from 'react';
import { X, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const AppointmentModal = ({ 
  isOpen, 
  onClose, 
  appointment, 
  patients, 
  formData, 
  setFormData, 
  onSave,
  onRefresh 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showPatientForm, setShowPatientForm] = useState(false);
  const [newPatientData, setNewPatientData] = useState({
    nom: '',
    prenom: '',
    telephone: ''
  });

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Auto-confirmation WhatsApp function
  const sendAutoConfirmation = async (appointmentData, patient) => {
    // Only send auto-confirmation if patient has WhatsApp number
    if (!patient?.numero_whatsapp) {
      console.log('Patient has no WhatsApp number, skipping auto-confirmation');
      return;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/whatsapp-hub/send-confirmation`, {
        patient_id: patient.id || appointmentData.patient_id,
        appointment_id: appointmentData.id,
        appointment_data: appointmentData
      });

      if (response.data.whatsapp_link) {
        // Show success message with option to open WhatsApp
        toast.success(
          <div>
            <p>RDV créé avec succès !</p>
            <button
              onClick={() => window.open(response.data.whatsapp_link, '_blank')}
              className="mt-2 text-green-600 underline hover:text-green-700"
            >
              📱 Ouvrir WhatsApp pour confirmer
            </button>
          </div>,
          { duration: 5000 }
        );
      }
    } catch (error) {
      console.error('Error sending auto-confirmation:', error);
      // Don't show error to user for auto-confirmation failure
      console.log('Auto-confirmation failed, but appointment was created successfully');
    }
  };

  // Pre-fill patient when modal opens from patient list (formData has patient_id)
  useEffect(() => {
    if (isOpen && formData.patient_id && patients.length > 0) {
      const selectedPatient = patients.find(patient => patient.id === formData.patient_id);
      if (selectedPatient) {
        setSearchTerm(`${selectedPatient.prenom} ${selectedPatient.nom}`);
      }
    } else if (!isOpen) {
      // Reset search when modal closes
      setSearchTerm('');
    }
  }, [isOpen, formData.patient_id, patients]);

  // Filter patients based on search term
  const filteredPatients = patients.filter(patient => 
    `${patient.prenom} ${patient.nom}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handlePatientSelect = (patient) => {
    setFormData(prev => ({ ...prev, patient_id: patient.id }));
    setSearchTerm(`${patient.prenom} ${patient.nom}`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation des champs obligatoires
    if (!formData.date || !formData.heure) {
      toast.error('Veuillez remplir la date et l\'heure');
      return;
    }
    
    // Si on est en mode "nouveau patient", créer le patient d'abord
    if (showPatientForm) {
      // Validation des données du nouveau patient
      if (!newPatientData.nom || !newPatientData.prenom) {
        toast.error('Veuillez remplir le nom et le prénom du patient');
        return;
      }
      
      try {
        // Créer le nouveau patient
        const response = await fetch(`${API_BASE_URL}/api/patients`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newPatientData),
        });

        if (response.ok) {
          const newPatient = await response.json();
          console.log('Patient created:', newPatient);
          
          // Créer le RDV immédiatement avec le nouveau patient
          const appointmentData = {
            patient_id: newPatient.patient_id, // Utiliser patient_id retourné par l'API
            date: formData.date,
            heure: formData.heure,
            type_rdv: formData.type_rdv,
            motif: formData.motif,
            notes: formData.notes,
            statut: 'programme'
          };
          
          console.log('Creating appointment with data:', appointmentData);
          
          // Appeler onSave avec les données mises à jour et attendre le résultat
          const result = await onSave(appointmentData);
          
          if (result && result.success) {
            // Nettoyer le formulaire nouveau patient seulement en cas de succès
            setShowPatientForm(false);
            setNewPatientData({ nom: '', prenom: '', telephone: '' });
            toast.success('Patient créé et rendez-vous programmé avec succès');
            
            // Send auto-confirmation WhatsApp
            await sendAutoConfirmation(result.appointment || appointmentData, newPatient);
          } else {
            toast.error('Erreur lors de la création du rendez-vous: ' + (result?.error || 'Erreur inconnue'));
          }
        } else {
          toast.error('Erreur lors de la création du patient');
        }
      } catch (error) {
        console.error('Error creating patient:', error);
        toast.error('Erreur lors de la création du patient');
      }
    } else {
      // Mode normal - vérifier qu'un patient est sélectionné
      if (!formData.patient_id) {
        toast.error('Veuillez sélectionner un patient');
        return;
      }
      
      const result = await onSave(formData);
      
      // Send auto-confirmation for existing patients
      if (result && result.success) {
        const selectedPatient = patients.find(p => p.id === formData.patient_id);
        if (selectedPatient) {
          await sendAutoConfirmation(result.appointment || formData, selectedPatient);
        }
      }
      
      // Le modal se ferme automatiquement en cas de succès dans handleCreateAppointment
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {appointment ? 'Modifier le rendez-vous' : 'Nouveau rendez-vous'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Patient Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Patient
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Tapez le nom du patient - Écriture manuscrite supportée"
                  className="search-stylus w-full pr-10"
                  inputMode="text"
                  autoCapitalize="words"
                  autoComplete="off"
                />
                <Search className="absolute right-3 top-2.5 w-5 h-5 text-gray-400" />
              </div>

              {/* Patient suggestions */}
              {searchTerm && filteredPatients.length > 0 && (
                <div className="mt-2 border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                  {filteredPatients.slice(0, 5).map(patient => (
                    <button
                      key={patient.id}
                      type="button"
                      onClick={() => handlePatientSelect(patient)}
                      className="w-full text-left px-3 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
                    >
                      {patient.prenom} {patient.nom}
                    </button>
                  ))}
                </div>
              )}

              {/* New Patient Toggle */}
              <div className="mt-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showPatientForm}
                    onChange={(e) => setShowPatientForm(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Nouveau patient</span>
                </label>
              </div>

              {/* New Patient Form */}
              {showPatientForm && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-gray-900 mb-3">Créer un nouveau patient</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Nom - Écriture manuscrite supportée"
                      value={newPatientData.nom}
                      onChange={(e) => setNewPatientData(prev => ({ ...prev, nom: e.target.value }))}
                      className="input-stylus"
                      inputMode="text"
                      autoCapitalize="words"
                      autoComplete="family-name"
                    />
                    <input
                      type="text"
                      placeholder="Prénom - Écriture manuscrite supportée"
                      value={newPatientData.prenom}
                      onChange={(e) => setNewPatientData(prev => ({ ...prev, prenom: e.target.value }))}
                      className="input-stylus"
                      inputMode="text"
                      autoCapitalize="words"
                      autoComplete="given-name"
                    />
                    <input
                      type="text"
                      placeholder="Téléphone - Écriture manuscrite supportée"
                      value={newPatientData.telephone}
                      onChange={(e) => setNewPatientData(prev => ({ ...prev, telephone: e.target.value }))}
                      className="input-stylus"
                      inputMode="tel"
                      autoComplete="tel"
                    />
                  </div>
                  <p className="mt-3 text-sm text-gray-600">
                    Utilisez le bouton "Créer patient + RDV" ci-dessous pour créer le patient et le rendez-vous en une seule action.
                  </p>
                </div>
              )}
            </div>

            {/* Date and Time */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Heure
                </label>
                <input
                  type="time"
                  value={formData.heure}
                  onChange={(e) => setFormData(prev => ({ ...prev, heure: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>
            </div>

            {/* Type and Motif */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type de RDV
                </label>
                <select
                  value={formData.type_rdv}
                  onChange={(e) => setFormData(prev => ({ ...prev, type_rdv: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="visite">Visite</option>
                  <option value="controle">Contrôle</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Motif
                </label>
                <input
                  type="text"
                  value={formData.motif}
                  onChange={(e) => setFormData(prev => ({ ...prev, motif: e.target.value }))}
                  placeholder="Motif de la consultation - Écriture manuscrite supportée"
                  className="input-stylus"
                  inputMode="text"
                  autoCapitalize="sentences"
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Notes additionnelles - Optimisé pour Apple Pencil"
                rows={3}
                className="textarea-stylus"
                inputMode="text"
                autoCapitalize="sentences"
              />
            </div>

            {/* Actions */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded-lg transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
              >
                {appointment ? 'Modifier' : showPatientForm ? 'Créer patient + RDV' : 'Créer RDV'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AppointmentModal;