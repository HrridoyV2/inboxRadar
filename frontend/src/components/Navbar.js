import React from 'react';
import { Sparkles, Bell, RefreshCw } from 'lucide-react';

export default function Navbar({
  wsStatus,
  notificationsEnabled,
  bellRinging,
  onRequestNotifications,
  onTriggerScan,
  polling
}) {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon-wrapper">
          <img 
            src="https://i.postimg.cc/NFf39kf7/99bf8e7b-fc1e-478a-9f0a-d5b4d34b58d4-removebg-preview.png" 
            alt="Logo" 
            style={{ width: '2rem', height: '2rem', borderRadius: '4px', objectFit: 'cover' }} 
          />
          <div className="brand-glow-dot"></div>
        </div>
        <div>
          <h1 className="brand-title">InboxRadar<span className="text-gradient ml-1">AI</span></h1>
          <p className="brand-subtitle">Autonomous Email Reading & Classification Agent</p>
        </div>
      </div>

      <div className="navbar-center">
        <div className="badge badge-neutral" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ 
            width: '6px', 
            height: '6px', 
            borderRadius: '50%', 
            background: wsStatus === 'connected' ? '#10b981' : '#f59e0b',
            marginRight: '6px'
          }}></span>
          WS: {wsStatus}
        </div>

        <button 
          onClick={onRequestNotifications} 
          className="btn-secondary"
          style={{ 
            fontSize: '0.725rem', 
            color: notificationsEnabled ? '#10b981' : '#cbd5e1',
            borderColor: notificationsEnabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.06)'
          }}
        >
          <Bell className={bellRinging ? 'animate-ring' : ''} style={{ width: '0.8rem', height: '0.8rem' }} />
          {notificationsEnabled ? 'Alerts Enabled' : 'Enable Alerts'}
        </button>

        <button 
          disabled={polling}
          onClick={onTriggerScan}
          className="btn-primary"
          style={{ fontSize: '0.725rem', padding: '0.45rem 0.875rem' }}
        >
          <RefreshCw className={polling ? 'animate-spin' : ''} style={{ width: '0.8rem', height: '0.8rem' }} />
          Scan Inbox
        </button>
      </div>

      <div className="navbar-actions" style={{ width: '180px' }}>
        {/* Empty placeholder to keep layout balanced or for future profile/settings */}
      </div>
    </header>
  );
}
