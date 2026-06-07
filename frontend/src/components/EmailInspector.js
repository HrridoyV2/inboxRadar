import React from 'react';
import { Mail, Sparkles } from 'lucide-react';

export default function EmailInspector({ selectedEmail, onClose }) {
  return (
    <div className="inspector-details">
      <div className="right-panel-header">
        <h2 className="right-panel-title">
          <Mail style={{ width: '1rem', height: '1rem', color: '#818cf8' }} />
          Email Inspector
        </h2>
        <button 
          onClick={onClose} 
          className="btn-close"
          title="Close Inspector"
        >
          &times;
        </button>
      </div>

      <div className="inspector-meta">
        <div style={{ display: 'flex', gap: '0.375rem', marginBottom: '0.25rem' }}>
          <span className={`badge ${
            selectedEmail.is_important
              ? selectedEmail.priority === 'HIGH' ? 'badge-high' :
                selectedEmail.priority === 'MEDIUM' ? 'badge-medium' : 'badge-low'
              : 'badge-neutral'
          }`}>
            {selectedEmail.is_important ? `${selectedEmail.priority} Priority` : 'Normal Priority'}
          </span>
          <span className="badge badge-neutral">
            {selectedEmail.category || 'OTHER'}
          </span>
        </div>
        <h3 className="inspector-subject">{selectedEmail.subject || '(No Subject)'}</h3>
        <div className="inspector-row" style={{ marginTop: '0.5rem' }}>
          <span className="inspector-label">From:</span> {selectedEmail.sender}
        </div>
        <div className="inspector-row">
          <span className="inspector-label">Received:</span> {new Date(selectedEmail.received_at).toLocaleString()}
        </div>
        <div className="inspector-row" style={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>
          <span className="inspector-label">Message ID:</span> {selectedEmail.message_id}
        </div>
      </div>

      {selectedEmail.reason && (
        <div className="form-group">
          <h4 className="form-label" style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles style={{ width: '0.8rem', height: '0.8rem' }} />
            AI Reasoning Verdict
          </h4>
          <div className="inspector-reason-box">
            {selectedEmail.reason}
          </div>
        </div>
      )}

      <div className="form-group" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <h4 className="form-label" style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Mail style={{ width: '0.8rem', height: '0.8rem' }} />
          Full Email Body
        </h4>
        <div className="inspector-body-box">
          {selectedEmail.body || '(Empty body)'}
        </div>
      </div>
    </div>
  );
}
