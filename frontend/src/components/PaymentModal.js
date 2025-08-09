import React, { useState, useEffect } from 'react';
import { 
  CreditCard, 
  DollarSign, 
  X, 
  Check, 
  AlertCircle,
  Info
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const PaymentModal = ({ 
  isOpen, 
  onClose, 
  appointment, 
  onPaymentUpdate,
  API_BASE_URL,
  user
}) => {
  const [paymentData, setPaymentData] = useState({
    paye: false,
    montant: 0,
    type_paiement: 'espece', // Toujours espèces
    assure: false,
    notes: '',
    type_rdv: 'visite' // Added to allow changing consultation type
  });
  
  const [loading, setLoading] = useState(false);

  // Fonction pour déterminer si le paiement peut être modifié par la secrétaire
  const canSecretaryModifyPayment = () => {
    // Si l'utilisateur est médecin, il peut toujours modifier
    if (user?.role === 'medecin') {
      return true;
    }
    
    // Si l'utilisateur est secrétaire
    if (user?.role === 'secretaire') {
      // Si la consultation n'est pas terminée, la secrétaire peut modifier
      if (appointment?.statut !== 'termine') {
        return true;
      }
      
      // Si la consultation est terminée, vérifier le statut de paiement
      if (appointment?.statut === 'termine') {
        // Pour les visites terminées :
        // - Si "non payé", la secrétaire peut encore modifier
        // - Si "payé" ou autre statut défini, la secrétaire ne peut plus modifier
        return !appointment?.paye;
      }
    }
    
    // Par défaut, autoriser la modification
    return true;
  };

  const canModifyPayment = canSecretaryModifyPayment();

  // Initialize payment data when modal opens
  useEffect(() => {
    if (isOpen && appointment) {
      // Set default amount based on appointment type - 65 TND par défaut
      const defaultAmount = appointment.type_rdv === 'visite' ? 65 : 0;
      
      setPaymentData({
        paye: appointment.paye || false,
        montant: appointment.paye ? (appointment.montant_paye || defaultAmount) : defaultAmount,
        type_paiement: 'espece', // Toujours espèces
        assure: appointment.assure || false,
        notes: '',
        type_rdv: appointment.type_rdv || 'visite' // Initialize with current type
      });
    }
  }, [isOpen, appointment]);

  // Handle consultation type change
  const handleConsultationTypeChange = (newType) => {
    setPaymentData(prev => ({
      ...prev,
      type_rdv: newType,
      montant: newType === 'visite' ? 65 : 0, // Auto-adjust amount
      paye: newType === 'controle' ? true : prev.paye // Contrôles are automatically handled as paid by backend
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Validate data
      if (paymentData.paye && paymentData.montant <= 0 && paymentData.type_rdv === 'visite') {
        toast.error('Le montant doit être supérieur à 0 pour une visite payée');
        return;
      }

      // Prepare complete payment data including type change
      const updateData = {
        ...paymentData,
        type_rdv: paymentData.type_rdv // Include the potentially changed consultation type
      };

      // Call API to update payment AND consultation type
      await axios.put(`${API_BASE_URL}/api/rdv/${appointment.id}/paiement`, updateData);
      
      toast.success('Paiement et type de consultation mis à jour avec succès');
      
      // Callback to parent component BEFORE closing
      if (onPaymentUpdate) {
        onPaymentUpdate(appointment.id, updateData);
      }
      
      // Close modal after callback
      onClose();
      
    } catch (error) {
      console.error('Error updating payment:', error);
      toast.error('Erreur lors de la mise à jour du paiement');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !appointment) return null;

  const isControle = paymentData.type_rdv === 'controle';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CreditCard className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Gestion Paiement</h2>
                <p className="text-sm text-gray-600">
                  {appointment.patient?.prenom} {appointment.patient?.nom}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Appointment Info */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-600">Type de RDV:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                  paymentData.type_rdv === 'controle' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {paymentData.type_rdv === 'controle' ? 'Contrôle' : 'Visite'}
                </span>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">Date & Heure</div>
                <div className="font-medium">{appointment.date} à {appointment.heure}</div>
              </div>
            </div>
          </div>

          {/* Type de consultation - Editable */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type de consultation
            </label>
            <div className="flex space-x-4 mb-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="type_rdv"
                  checked={paymentData.type_rdv === 'visite'}
                  onChange={() => handleConsultationTypeChange('visite')}
                  disabled={!canModifyPayment}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Visite (65 TND)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="type_rdv"
                  checked={paymentData.type_rdv === 'controle'}
                  onChange={() => handleConsultationTypeChange('controle')}
                  disabled={!canModifyPayment}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Contrôle (Gratuit)</span>
              </label>
            </div>
          </div>

          {/* Contrôle Info */}
          {isControle && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <Info className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-800">Consultation Contrôle</p>
                  <p className="text-sm text-green-600">
                    Les consultations de contrôle sont automatiquement gratuites.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Message de restriction pour secrétaire */}
          {!canModifyPayment && user?.role === 'secretaire' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">🔒 Paiement verrouillé</p>
                  <p className="text-sm text-red-600">
                    Cette consultation est terminée et son statut de paiement a été déterminé. 
                    Seul le médecin peut modifier le paiement à ce stade pour des raisons de sécurité.
                  </p>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleSave(); }} className="space-y-4">
            {/* Payment Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Statut du paiement
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="paye"
                    checked={paymentData.paye}
                    onChange={() => setPaymentData(prev => ({ ...prev, paye: true }))}
                    disabled={paymentData.type_rdv === 'controle' || !canModifyPayment}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Payé</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="paye"
                    checked={!paymentData.paye}
                    onChange={() => setPaymentData(prev => ({ ...prev, paye: false }))}
                    disabled={paymentData.type_rdv === 'controle' || !canModifyPayment}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Non payé</span>
                </label>
              </div>
            </div>

            {/* Payment Amount */}
            <div>
              <label htmlFor="montant" className="block text-sm font-medium text-gray-700 mb-2">
                Montant (TND)
              </label>
              <input
                type="number"
                id="montant"
                step="0.01"
                min="0"
                value={paymentData.montant}
                onChange={(e) => setPaymentData(prev => ({ 
                  ...prev, 
                  montant: parseFloat(e.target.value) || 0 
                }))}
                disabled={paymentData.type_rdv === 'controle' || !canModifyPayment}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            {/* Méthode de paiement - Toujours espèces */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Méthode de paiement
              </label>
              <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700">
                💵 Espèces (TND)
              </div>
            </div>

            {/* Insurance - Simplifié */}
            <div>
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="assure"
                  checked={paymentData.assure}
                  onChange={(e) => setPaymentData(prev => ({ 
                    ...prev, 
                    assure: e.target.checked
                  }))}
                  disabled={!canModifyPayment}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:bg-gray-100"
                />
                <label htmlFor="assure" className="text-sm font-medium text-gray-700">
                  Patient assuré
                </label>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optionnel)
              </label>
              <textarea
                id="notes"
                rows="3"
                value={paymentData.notes}
                onChange={(e) => setPaymentData(prev => ({ 
                  ...prev, 
                  notes: e.target.value 
                }))}
                disabled={!canModifyPayment}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                placeholder={canModifyPayment ? "Notes sur le paiement..." : "Lecture seule - Seul le médecin peut modifier"}
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={loading || !canModifyPayment}
                className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center space-x-2 ${
                  canModifyPayment 
                    ? 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400'
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
                title={!canModifyPayment ? "Modification non autorisée pour la secrétaire" : ""}
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Check className="w-4 h-4" />
                )}
                <span>
                  {loading 
                    ? 'Sauvegarde...' 
                    : canModifyPayment 
                      ? 'Sauvegarder' 
                      : 'Lecture seule'
                  }
                </span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;