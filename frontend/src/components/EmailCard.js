import React from 'react';
import { Clock, Sparkles, ArrowRight } from 'lucide-react';

export default function EmailCard({ email, selectedEmail, onSelect }) {
  const isSelected = selectedEmail && selectedEmail.id === email.id;

  return (
    <div 
      onClick={() => onSelect(email)}
      className="alert-card"
      style={{
        borderColor: isSelected ? '#4f46e5' : 'rgba(255, 255, 255, 0.05)',
        background: isSelected ? 'rgba(79, 70, 229, 0.06)' : 'rgba(16, 21, 38, 0.4)'
      }}
    >
      <div className="alert-card-left-border" style={{
        backgroundColor: email.is_important
          ? email.priority === 'HIGH' ? 'var(--color-high)' :
            email.priority === 'MEDIUM' ? 'var(--color-medium)' : 'var(--color-low)'
          : 'var(--color-text-muted)'
      }}></div>

      <div className="card-header-line">
        <div className="card-meta-info">
          <div className="card-sender-row">
            <span style={{ color: '#ffffff', fontWeight: '600' }}>{email.sender}</span>
            <span>&bull;</span>
            <span className="card-timestamp-wrapper">
              <Clock style={{ width: '0.7rem', height: '0.7rem' }} />
              {new Date(email.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <h4 className="card-subject">{email.subject || '(No Subject)'}</h4>
        </div>

        <div className="card-badges-wrapper">
          <span className="badge badge-neutral">
            {email.category || 'OTHER'}
          </span>
          {email.is_important && (
            <span className={`badge ${
              email.priority === 'HIGH' ? 'badge-high' :
              email.priority === 'MEDIUM' ? 'badge-medium' : 'badge-low'
            }`}>
              {email.priority}
            </span>
          )}
        </div>
      </div>

      {email.reason && (
        <div className="card-ai-verdict">
          <Sparkles style={{ width: '0.8rem', height: '0.8rem' }} />
          <p><strong>AI Reason:</strong> {email.reason}</p>
        </div>
      )}

      <div className="card-footer-line">
        <span className="card-body-snippet">
          {email.body ? email.body : '(Empty body)'}
        </span>
        <span className="card-details-link">
          Inspect
          <ArrowRight style={{ width: '0.75rem', height: '0.75rem' }} />
        </span>
      </div>
    </div>
  );
}
