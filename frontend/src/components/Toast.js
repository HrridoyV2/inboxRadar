import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Toast({
  message,
  type = 'info',
  onClose,
  duration = 5000
}) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const bgColors = {
    success: {
      bg: '#059669',
      border: '#10b981'
    },
    error: {
      bg: '#e11d48',
      border: '#f43f5e'
    },
    warning: {
      bg: '#d97706',
      border: '#fbbf24'
    },
    info: {
      bg: '#2563eb',
      border: '#3b82f6'
    },
    alert: {
      bg: '#7c3aed',
      border: '#8b5cf6'
    }
  };

  const styleObj = bgColors[type] || bgColors.info;

  return (
    <div
      className="flex items-center py-3 pr-3 pl-8 text-sm border rounded-lg shadow-2xl animate-slide-in-right text-white min-w-[280px]"
      style={{
        backgroundColor: styleObj.bg,
        borderColor: styleObj.border
      }}
      role="alert"
    >
      <div className="font-medium flex-1">
        {message}
      </div>

      <button
        type="button"
        className="ml-3 p-0.5 text-white/80 hover:text-white transition-colors"
        onClick={onClose}
        aria-label="Close"
      >
        <X size={18} />
      </button>
    </div>
  );
}