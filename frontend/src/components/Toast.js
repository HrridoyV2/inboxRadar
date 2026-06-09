import React, { useEffect } from 'react';
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-react';

export default function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-emerald-500" />,
    error: <XCircle className="w-5 h-5 text-rose-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />,
    alert: <CheckCircle className="w-5 h-5 text-purple-500" />
  };

  const bgColors = {
    success: { bg: '#059669', border: '#10b981' },
    error: { bg: '#e11d48', border: '#f43f5e' },
    warning: { bg: '#d97706', border: '#fbbf24' },
    info: { bg: '#2563eb', border: '#3b82f6' },
    alert: { bg: '#7c3aed', border: '#8b5cf6' }
  };

  const styleObj = bgColors[type] || bgColors.info;

  return (
    <div 
      className="flex items-center p-3 mb-4 text-sm border rounded-lg shadow-2xl animate-slide-in-right whitespace-nowrap text-white" 
      style={{ backgroundColor: styleObj.bg, borderColor: styleObj.border }}
      role="alert"
    >
      <div className="flex-shrink-0 flex items-center justify-center">
        {React.cloneElement(icons[type] || icons.info, { className: 'w-4 h-4 text-white' })}
      </div>
      <div className="mx-3 font-semibold">
        {message}
      </div>
      <button
        type="button"
        className="ml-auto p-1 flex items-center justify-center text-white/80 hover:text-white rounded-lg focus:ring-2 focus:ring-white/20 transition-colors"
        onClick={onClose}
        aria-label="Close"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
