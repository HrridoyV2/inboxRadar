import React from 'react';
import { Terminal, FileCode, Send, ArrowRight } from 'lucide-react';

export default function SandboxControls({
  mockDataset,
  selectedMockId,
  setSelectedMockId,
  onSimulateMock,
  smtpSubject,
  setSmtpSubject,
  smtpBody,
  setSmtpBody,
  onSendTestSmtp,
  emailUser
}) {
  return (
    <>
      <div className="right-panel-header">
        <h2 className="right-panel-title">
          <Terminal style={{ width: '1rem', height: '1rem', color: '#818cf8' }} />
          Sandbox Controls
        </h2>
      </div>

      {/* Trigger 3: Simulation */}
      <div className="control-section">
        <h3 className="control-section-header">
          <FileCode style={{ width: '0.875rem', height: '0.875rem', color: '#a855f7' }} />
          Simulator Ingest (Trigger 3)
        </h3>
        <p style={{ fontSize: '0.725rem', color: '#64748b', margin: '0.25rem 0' }}>
          Inject pre-configured scenarios directly to run AI classification.
        </p>

        <div className="form-group" style={{ margin: '0.5rem 0' }}>
          <label className="form-label">Email Template</label>
          <select 
            value={selectedMockId} 
            onChange={(e) => setSelectedMockId(e.target.value)}
            className="form-control"
          >
            {mockDataset.map(item => (
              <option key={item.id} value={item.id}>
                {item.subject}
              </option>
            ))}
          </select>
        </div>

        <button 
          onClick={onSimulateMock} 
          className="btn-primary"
          style={{ width: '100%' }}
        >
          Trigger Simulation
          <ArrowRight style={{ width: '0.8rem', height: '0.8rem' }} />
        </button>
      </div>

      {/* Trigger 2: SMTP Sender */}
      <form onSubmit={onSendTestSmtp} className="control-section">
        <h3 className="control-section-header">
          <Send style={{ width: '0.875rem', height: '0.875rem', color: '#6366f1' }} />
          SMTP Send Test (Trigger 2)
        </h3>
        <p style={{ fontSize: '0.725rem', color: '#64748b', margin: '0.25rem 0' }}>
          Simulates sending a custom email to self. Processed instantly.
        </p>
        <div style={{ fontSize: '0.7rem', color: '#818cf8', fontWeight: '600', marginBottom: '0.5rem' }}>
          Target: {emailUser || 'Not Configured'}
        </div>

        <div className="form-group">
          <label className="form-label">Subject</label>
          <input 
            type="text" 
            placeholder="Enter email subject..." 
            value={smtpSubject}
            onChange={(e) => setSmtpSubject(e.target.value)}
            className="form-control"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Body Content</label>
          <textarea 
            rows="4" 
            placeholder="Write custom body content..." 
            value={smtpBody}
            onChange={(e) => setSmtpBody(e.target.value)}
            className="form-control"
            required
          />
        </div>

        <button 
          type="submit" 
          className="btn-secondary"
          style={{ width: '100%' }}
        >
          Send Custom Email
          <Send style={{ width: '0.75rem', height: '0.75rem' }} />
        </button>
      </form>
    </>
  );
}
