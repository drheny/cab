import React, { useState, useRef, useEffect } from 'react';
import { Edit3, Type, Wand2, Save, RotateCcw } from 'lucide-react';

const HandwritingField = ({ 
  value, 
  onChange, 
  placeholder, 
  className = "",
  rows = 6,
  enableOCR = true,
  medicalContext = false,
  disableHandwriting = false
}) => {
  const [mode, setMode] = useState('typing'); // 'typing' | 'handwriting'
  const [isProcessing, setIsProcessing] = useState(false);
  const [handwritingData, setHandwritingData] = useState(null);
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);

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
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#1f2937';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  // OCR et auto-raffinement IA
  const refineHandwriting = async () => {
    if (!canvasRef.current) return;

    setIsProcessing(true);
    try {
      const canvas = canvasRef.current;
      const imageData = canvas.toDataURL('image/png');
      
      // Appel API OCR + Refinement IA médical
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
        })
      });

      const result = await response.json();
      
      if (result.success) {
        // Mise à jour avec le texte raffiné
        onChange(result.refinedText);
        
        // Optionnel: conserver l'image originale
        setHandwritingData({
          originalImage: imageData,
          extractedText: result.extractedText,
          refinedText: result.refinedText,
          confidence: result.confidence
        });
      }
      
    } catch (error) {
      console.error('Handwriting refinement failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const toggleMode = () => {
    const newMode = mode === 'typing' ? 'handwriting' : 'typing';
    setMode(newMode);
    
    // Si passage en mode manuscrit, configurer le canvas
    if (newMode === 'handwriting') {
      setTimeout(() => {
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = canvas.offsetWidth;
          canvas.height = canvas.offsetHeight;
        }
      }, 100);
    }
  };

  const currentConfig = mode === 'handwriting' ? handwritingConfig : typingConfig;

  return (
    <div className="relative">
      {/* Toggle Mode */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex space-x-2">
          <button
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
              onClick={clearCanvas}
              className="p-1 rounded text-gray-500 hover:text-gray-700"
              title="Effacer"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            
            {enableOCR && (
              <button
                onClick={refineHandwriting}
                disabled={isProcessing}
                className="flex items-center space-x-1 px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm hover:bg-purple-200 transition-all disabled:opacity-50"
                title="Auto-raffinement IA"
              >
                <Wand2 className="w-4 h-4" />
                {isProcessing ? 'Traitement...' : 'Raffiner'}
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
            onTouchStart={(e) => startDrawing(e.touches[0])}
            onTouchMove={(e) => {
              e.preventDefault();
              draw(e.touches[0]);
            }}
            onTouchEnd={stopDrawing}
            style={{ 
              zIndex: mode === 'handwriting' ? 10 : -1,
              cursor: 'crosshair'
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