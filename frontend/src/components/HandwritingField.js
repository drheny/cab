import React, { useState, useRef, useEffect } from 'react';
import { Edit3, Type, Wand2, Save, RotateCcw, Eraser } from 'lucide-react';

const HandwritingField = ({ 
  value, 
  onChange, 
  placeholder, 
  className = "",
  rows = 6,
  enableOCR = true,
  medicalContext = false,
  onFormInteraction = () => {}, // Callback pour contrôler la prévention des soumissions de formulaire
  // NOUVEAUX PROPS POUR GÉRER LES DONNÉES MANUSCRITES
  savedHandwritingData = "", // Base64 image data du canvas depuis la DB
  onHandwritingDataChange = () => {}, // Callback pour sauvegarder les données du canvas
  initialMode = "typing", // Mode initial depuis la base de données
  onModeChange = () => {} // Callback pour sauvegarder le mode
}) => {
  const [mode, setMode] = useState(initialMode); // Use initial mode from database
  const [isProcessing, setIsProcessing] = useState(false);
  const [handwritingData, setHandwritingData] = useState(null);
  const [isErasing, setIsErasing] = useState(false); // New eraser mode
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);

  // EFFET POUR RESTAURER LES DONNÉES DU CANVAS DEPUIS LA BASE DE DONNÉES
  useEffect(() => {
    if (savedHandwritingData && mode === 'handwriting' && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
      img.src = savedHandwritingData;
    }
  }, [savedHandwritingData, mode]);

  // EFFET POUR SAUVEGARDER LES DONNÉES DU CANVAS
  const saveCanvasData = () => {
    if (mode === 'handwriting' && canvasRef.current) {
      const canvas = canvasRef.current;
      const imageData = canvas.toDataURL('image/png');
      onHandwritingDataChange(imageData);
    }
  };

  // Configuration différentielle selon le mode
  const typingConfig = {
    className: "textarea-stylus bg-white",
    inputMode: "text",
    autoCapitalize: "sentences",
    spellCheck: true,
  };

  const handwritingConfig = {
    className: "textarea-stylus bg-striped-paper border-2 border-blue-200",
    inputMode: "none", // Désactive le clavier virtuel
    autoCapitalize: "off",
    spellCheck: false,
    style: {
      backgroundImage: `repeating-linear-gradient(
        transparent,
        transparent 24px,
        #e5e7eb 24px,
        #e5e7eb 25px
      )`,
      lineHeight: '25px',
      paddingTop: '4px'
    }
  };

  // Canvas pour capture d'écriture manuscrite
  const startDrawing = (e) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Gérer à la fois mouse et touch events
    const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : e.pageX);
    const clientY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : e.pageY);
    
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
    
    // Set the appropriate drawing mode
    if (isErasing) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.lineWidth = 10;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.lineWidth = 2;
    }
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Gérer à la fois mouse et touch events
    const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : e.pageX);
    const clientY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : e.pageY);
    
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    
    if (isErasing) {
      // Eraser mode - use clear/destination-out blend mode
      ctx.globalCompositeOperation = 'destination-out';
      ctx.lineWidth = 10; // Larger eraser size
    } else {
      // Drawing mode - normal drawing
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 2;
    }
    
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  // OCR et auto-raffinement IA
  const refineHandwriting = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Prévenir la soumission du formulaire
    onFormInteraction(true);
    
    if (!canvasRef.current) {
      onFormInteraction(false);
      return;
    }

    setIsProcessing(true);
    
    try {
      const canvas = canvasRef.current;
      const imageData = canvas.toDataURL('image/png');
      
      console.log('🎨 Début du raffinement IA...');
      
      // Appel API OCR + Refinement IA médical avec timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 secondes timeout
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ai/refine-handwriting`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageData,
          currentText: value,
          medicalContext,
          language: 'fr'
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      console.log('🤖 Résultat IA:', result);
      
      if (result.success && result.refinedText && result.refinedText !== value) {
        // Mise à jour avec le texte raffiné seulement s'il y a une amélioration
        onChange(result.refinedText);
        
        // Conserver l'image et métadonnées
        setHandwritingData({
          originalImage: imageData,
          extractedText: result.extractedText,
          refinedText: result.refinedText,
          confidence: result.confidence,
          method: result.method
        });
        
        console.log(`✅ Texte raffiné avec ${result.confidence}% de confiance (${result.method})`);
      } else {
        console.log('⚠️ Pas d\'amélioration trouvée par l\'IA');
      }
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('⏱️ Timeout: Le raffinement IA a pris trop de temps');
      } else {
        console.error('❌ Échec du raffinement IA:', error);
      }
    } finally {
      setIsProcessing(false);
      // Désactiver la prévention après traitement
      setTimeout(() => {
        onFormInteraction(false);
      }, 200);
    }
  };

  const clearCanvas = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Prévenir la soumission du formulaire
    onFormInteraction(true);
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Reset composite operation to default
    ctx.globalCompositeOperation = 'source-over';
    
    // Désactiver la prévention après un court délai
    setTimeout(() => {
      onFormInteraction(false);
    }, 200);
  };

  const toggleEraser = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Prévenir la soumission du formulaire
    onFormInteraction(true);
    setIsErasing(!isErasing);
    
    // Désactiver la prévention après un court délai
    setTimeout(() => {
      onFormInteraction(false);
    }, 200);
  };

  const toggleMode = (e) => {
    // Proper event prevention for React SyntheticEvent
    e.preventDefault();
    e.stopPropagation();
    
    console.log('🔄 HandwritingField toggleMode called - preventing form submission');
    
    // Activer la prévention de soumission du formulaire
    onFormInteraction(true);
    
    // Sauvegarder les données du canvas avant le changement de mode
    saveCanvasData();
    
    const newMode = mode === 'typing' ? 'handwriting' : 'typing';
    console.log(`🔄 Switching from ${mode} to ${newMode}`);
    setMode(newMode);
    
    // Notifier le parent du changement de mode
    onModeChange(newMode);
    
    // Si passage en mode manuscrit, configurer le canvas
    if (newMode === 'handwriting') {
      setTimeout(() => {
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = canvas.offsetWidth;
          canvas.height = canvas.offsetHeight;
          console.log('🎨 Canvas configured for handwriting mode');
          
          // Restaurer les données sauvegardées
          if (savedHandwritingData) {
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.onload = () => {
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = savedHandwritingData;
          }
        }
      }, 100);
    }
    
    // Désactiver la prévention après un délai plus long pour être sûr
    setTimeout(() => {
      onFormInteraction(false);
      console.log('✅ Form submission prevention disabled');
    }, 1000);
    
    // Return false to be extra sure
    return false;
  };

  const currentConfig = mode === 'handwriting' ? handwritingConfig : typingConfig;

  return (
    <div 
      className="relative"
      style={{
        // Empêcher le scroll et zoom tactile sur tout le conteneur en mode manuscrit
        touchAction: mode === 'handwriting' ? 'none' : 'auto'
      }}
    >
      {/* Toggle Mode - Wrapped in non-submitting container */}
      <div 
        className="flex justify-between items-center mb-2"
        onClick={(e) => {
          // Prevent any bubbling from this container
          e.preventDefault();
          e.stopPropagation();
        }}
        onSubmit={(e) => {
          // Extra safety - prevent submit events on this container
          e.preventDefault();
          e.stopPropagation();
          return false;
        }}
      >
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={toggleMode}
            className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-sm transition-all ${
              mode === 'typing' 
                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Type className="w-4 h-4" />
            <span>Saisie</span>
          </button>
          
          <button
            type="button"
            onClick={toggleMode}
            className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-sm transition-all ${
              mode === 'handwriting' 
                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Edit3 className="w-4 h-4" />
            <span>Manuscrit</span>
          </button>
        </div>

        {/* Actions spécifiques au mode manuscrit */}
        {mode === 'handwriting' && (
          <div className="flex space-x-1">
            <button
              type="button"
              onClick={toggleEraser}
              className={`p-1 rounded text-sm transition-all ${
                isErasing 
                  ? 'bg-red-100 text-red-700 border border-red-300' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              title="Gomme"
            >
              <Eraser className="w-4 h-4" />
            </button>
            
            <button
              type="button"
              onClick={clearCanvas}
              className="p-1 rounded text-gray-500 hover:text-gray-700"
              title="Effacer tout"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            
            {enableOCR && (
              <button
                type="button"
                onClick={refineHandwriting}
                disabled={isProcessing}
                className={`flex items-center space-x-1 px-2 py-1 rounded text-sm transition-all ${
                  isProcessing 
                    ? 'bg-purple-200 text-purple-600 cursor-not-allowed' 
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                }`}
                title="Auto-raffinement IA avec OCR"
              >
                <Wand2 className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                {isProcessing ? 'IA traite...' : 'Raffiner IA'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Zone de saisie */}
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={`${placeholder} - Mode ${mode === 'handwriting' ? 'manuscrit' : 'saisie'}`}
          rows={rows}
          className={`${currentConfig.className} ${className}`}
          inputMode={currentConfig.inputMode}
          autoCapitalize={currentConfig.autoCapitalize}
          spellCheck={currentConfig.spellCheck}
          style={currentConfig.style}
          autoComplete="off"
          data-gramm="false"
        />

        {/* Canvas superposé pour mode manuscrit */}
        {mode === 'handwriting' && (
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 w-full h-full pointer-events-auto bg-transparent"
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            onTouchStart={(e) => {
              e.preventDefault(); // Empêcher le scroll de la page
              e.stopPropagation(); // Empêcher la propagation
              startDrawing(e.touches[0]);
            }}
            onTouchMove={(e) => {
              e.preventDefault(); // CRITIQUE: Empêcher le scroll de la page
              e.stopPropagation();
              draw(e.touches[0]);
            }}
            onTouchEnd={(e) => {
              e.preventDefault(); // Empêcher le scroll de la page
              e.stopPropagation();
              stopDrawing();
            }}
            style={{ 
              zIndex: mode === 'handwriting' ? 10 : -1,
              cursor: isErasing ? 'crosshair' : 'crosshair',
              touchAction: 'none' // CRITIQUE: Désactiver complètement le scroll et zoom tactile
            }}
          />
        )}
      </div>

      {/* Indicateur de traitement */}
      {isProcessing && (
        <div className="absolute inset-0 bg-white bg-opacity-80 flex items-center justify-center">
          <div className="flex items-center space-x-2 text-purple-600">
            <Wand2 className="w-5 h-5 animate-pulse" />
            <span>Raffinement en cours...</span>
          </div>
        </div>
      )}

      {/* Résultats OCR (debug) */}
      {handwritingData && (
        <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
          <strong>Confiance OCR:</strong> {handwritingData.confidence}%
        </div>
      )}
    </div>
  );
};

export default HandwritingField;