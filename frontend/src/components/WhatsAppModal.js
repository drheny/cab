import React, { useState, useEffect } from 'react';
import { 
  MessageCircle, 
  Send, 
  X, 
  User, 
  Clock, 
  Edit3,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Copy,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const WhatsAppModal = ({ 
  isOpen, 
  onClose, 
  patient, 
  appointment, 
  queueContext = null 
}) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customMessage, setCustomMessage] = useState('');
  const [finalMessage, setFinalMessage] = useState('');
  const [whatsappLink, setWhatsappLink] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Select Template, 2: Edit Message, 3: Confirm Send

  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
      setStep(1);
      setSelectedTemplate(null);
      setCustomMessage('');
      setFinalMessage('');
    }
  }, [isOpen]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/whatsapp-hub/templates`);
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      toast.error('Erreur lors du chargement des templates');
    } finally {
      setLoading(false);
    }
  };

  const prepareMessage = async (templateId, customMsg = null) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/whatsapp-hub/prepare-message`, {
        patient_id: patient.id,
        template_id: templateId,
        custom_message: customMsg
      });

      setFinalMessage(response.data.message.content);
      setWhatsappLink(response.data.message.whatsapp_link);
      setAiSuggestions(response.data.ai_suggestions || []);
      
      // Move to edit step
      setStep(2);
      
    } catch (error) {
      console.error('Error preparing message:', error);
      toast.error('Erreur lors de la préparation du message');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setCustomMessage('');
    prepareMessage(template.id);
  };

  const handleCustomMessage = () => {
    if (customMessage.trim()) {
      setSelectedTemplate(null);
      prepareMessage(null, customMessage.trim());
    } else {
      toast.error('Veuillez saisir un message personnalisé');
    }
  };

  const handleMessageEdit = () => {
    setCustomMessage(finalMessage);
    prepareMessage(null, finalMessage);
  };

  const handleConfirmSend = () => {
    setStep(3);
  };

  const handleSendWhatsApp = () => {
    if (whatsappLink) {
      // Ouvrir WhatsApp Web avec le message pré-rempli
      window.open(whatsappLink, '_blank');
      
      // Notifier le succès et fermer le modal
      toast.success(`Message WhatsApp préparé pour ${patient.prenom} ${patient.nom}`);
      onClose();
    } else {
      toast.error('Erreur: Lien WhatsApp non disponible');
    }
  };

  const copyMessageToClipboard = () => {
    navigator.clipboard.writeText(finalMessage);
    toast.success('Message copié dans le presse-papiers');
  };

  const getTemplatesByCategory = () => {
    const categories = {};
    templates.forEach(template => {
      if (!categories[template.category]) {
        categories[template.category] = [];
      }
      categories[template.category].push(template);
    });
    return categories;
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'confirmation':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'attente':
        return <Clock className="w-5 h-5 text-blue-500" />;
      case 'ajustement':
        return <RefreshCw className="w-5 h-5 text-yellow-500" />;
      case 'urgence':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <MessageCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getCategoryLabel = (category) => {
    const labels = {
      'confirmation': 'Confirmation',
      'attente': 'Salle d\'attente',
      'ajustement': 'Ajustement RDV',
      'urgence': 'Urgence',
      'rappel': 'Rappel',
      'annulation': 'Annulation'
    };
    return labels[category] || category;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <MessageCircle className="w-8 h-8 text-green-500" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Message WhatsApp</h2>
              <p className="text-gray-600">
                {patient.prenom} {patient.nom} - {patient.numero_whatsapp}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 bg-gray-50">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-primary-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= 1 ? 'bg-primary-600 text-white' : 'bg-gray-200'
              }`}>
                1
              </div>
              <span className="font-medium">Template</span>
            </div>
            <div className="flex-1 h-px bg-gray-300"></div>
            <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-primary-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= 2 ? 'bg-primary-600 text-white' : 'bg-gray-200'
              }`}>
                2
              </div>
              <span className="font-medium">Message</span>
            </div>
            <div className="flex-1 h-px bg-gray-300"></div>
            <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-primary-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= 3 ? 'bg-primary-600 text-white' : 'bg-gray-200'
              }`}>
                3
              </div>
              <span className="font-medium">Envoi</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Step 1: Template Selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Choisir un Template</h3>
                
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(getTemplatesByCategory()).map(([category, categoryTemplates]) => (
                      <div key={category} className="border border-gray-200 rounded-lg">
                        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center space-x-2">
                          {getCategoryIcon(category)}
                          <h4 className="font-medium text-gray-900">{getCategoryLabel(category)}</h4>
                          <span className="text-sm text-gray-500">({categoryTemplates.length})</span>
                        </div>
                        <div className="p-4 space-y-3">
                          {categoryTemplates.map((template) => (
                            <div
                              key={template.id}
                              className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 cursor-pointer transition-colors"
                              onClick={() => handleTemplateSelect(template)}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <h5 className="font-medium text-gray-900">{template.name}</h5>
                                {template.auto_send && (
                                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                    Auto
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                                {template.content.substring(0, 150)}...
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Message personnalisé */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="font-medium text-gray-900 mb-3">Ou écrire un message personnalisé</h4>
                <div className="space-y-3">
                  <textarea
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.target.value)}
                    rows={4}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Tapez votre message personnalisé ici..."
                  />
                  <button
                    onClick={handleCustomMessage}
                    disabled={!customMessage.trim() || loading}
                    className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 transition-colors"
                  >
                    Utiliser ce message
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Message Editing */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Vérifier et Modifier le Message</h3>
                
                {/* AI Suggestions */}
                {aiSuggestions.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <h4 className="font-medium text-blue-900 mb-2">💡 Suggestions IA</h4>
                    <ul className="space-y-1">
                      {aiSuggestions.map((suggestion, index) => (
                        <li key={index} className="text-sm text-blue-700">
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Message Preview */}
                <div className="border border-gray-200 rounded-lg">
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                    <span className="font-medium text-gray-900">Aperçu du Message</span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={copyMessageToClipboard}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="Copier le message"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleMessageEdit}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="Modifier le message"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="bg-green-100 rounded-lg p-3 inline-block max-w-full">
                      <p className="text-gray-900 whitespace-pre-wrap">{finalMessage}</p>
                    </div>
                    <div className="mt-3 text-xs text-gray-500">
                      {finalMessage.length} caractères
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Retour
                </button>
                <button
                  onClick={handleConfirmSend}
                  className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>Préparer l'envoi WhatsApp</span>
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Confirmation */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Confirmer l'envoi WhatsApp</h3>
                <p className="text-gray-600">
                  Le message sera ouvert dans WhatsApp Web pour envoi à {patient.prenom} {patient.nom}
                </p>
              </div>

              {/* Final Message Display */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Message à envoyer :</h4>
                <div className="bg-green-100 rounded-lg p-3 inline-block max-w-full">
                  <p className="text-gray-900 whitespace-pre-wrap">{finalMessage}</p>
                </div>
              </div>

              {/* Patient Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <User className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="font-medium text-blue-900">
                      {patient.prenom} {patient.nom}
                    </p>
                    <p className="text-sm text-blue-700">{patient.numero_whatsapp}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setStep(2)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Modifier
                </button>
                <button
                  onClick={handleSendWhatsApp}
                  className="flex-1 bg-green-500 text-white py-3 px-6 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2 font-medium"
                >
                  <ExternalLink className="w-5 h-5" />
                  <span>Ouvrir WhatsApp Web</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WhatsAppModal;