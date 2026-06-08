import React from 'react';
import { Clock, Sparkles, ArrowRight } from 'lucide-react';

export default function EmailCard({ email, selectedEmail, onSelect }) {
  const isSelected = selectedEmail && selectedEmail.id === email.id;

  return (
    <div 
      onClick={() => onSelect(email)}
      className={`alert-card ${isSelected ? 'selected' : ''}`}
    >
      <div className="alert-card-left-border" style={{
        backgroundColor: email.is_important
          ? email.priority === 'HIGH' ? 'var(--color-high)' :
            email.priority === 'MEDIUM' ? 'var(--color-medium)' : 'var(--color-low)'
          : 'var(--color-text-muted)'
      }}></div>

      <div className="card-content-grid">
        {/* Column 1: Subject (Flexible) */}
        <div className="card-col-subject">
          <h4 className="card-subject">
            {email.subject || '(No Subject)'}
          </h4>
        </div>
        
        {/* Column 2: Sender (Fixed width area) */}
        <div className="card-col-sender">
          <span className="card-sender-text">
            {email.sender.split('<')[0].trim() || email.sender}
          </span>
        </div>

        {/* Column 3: Category & Priority */}
        <div className="card-col-badges">
          {email.is_important && (
            <span className={`badge ${
              email.priority === 'HIGH' ? 'badge-high' :
              email.priority === 'MEDIUM' ? 'badge-medium' : 'badge-low'
            }`}>
              {email.priority[0]}
            </span>
          )}
          <span className="badge badge-neutral">
            {email.category || 'OTHER'}
          </span>
        </div>

        {/* Column 4: Timestamp */}
        <div className="card-col-time">
          <span className="card-timestamp">
            {new Date(email.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
}
