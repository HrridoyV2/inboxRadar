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
        background: isSelected ? 'rgba(79, 70, 229, 0.06)' : 'rgba(16, 21, 38, 0.4)',
        padding: '0.625rem 1rem',
        minHeight: 'auto',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}
    >
      <div className="alert-card-left-border" style={{
        backgroundColor: email.is_important
          ? email.priority === 'HIGH' ? 'var(--color-high)' :
            email.priority === 'MEDIUM' ? 'var(--color-medium)' : 'var(--color-low)'
          : 'var(--color-text-muted)'
      }}></div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
        <h4 className="card-subject" style={{ 
          margin: 0, 
          textAlign: 'left', 
          fontSize: '0.85rem', 
          whiteSpace: 'nowrap', 
          overflow: 'hidden', 
          textOverflow: 'ellipsis',
          flex: 1
        }}>
          {email.subject || '(No Subject)'}
        </h4>
        
        <span style={{ 
          fontSize: '0.7rem', 
          color: 'var(--color-text-secondary)', 
          whiteSpace: 'nowrap',
          flexShrink: 0 
        }}>
          {email.sender.split('<')[0].trim() || email.sender}
        </span>
      </div>

      <div className="card-badges-wrapper" style={{ flexShrink: 0 }}>
        {email.is_important && (
          <span className={`badge ${
            email.priority === 'HIGH' ? 'badge-high' :
            email.priority === 'MEDIUM' ? 'badge-medium' : 'badge-low'
          }`}>
            {email.priority[0]}
          </span>
        )}
        <span className="badge badge-neutral" style={{ fontSize: '0.6rem' }}>
          {email.category || 'OTHER'}
        </span>
        <span className="card-timestamp-wrapper" style={{ marginLeft: '0.5rem', opacity: 0.6 }}>
          {new Date(email.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
