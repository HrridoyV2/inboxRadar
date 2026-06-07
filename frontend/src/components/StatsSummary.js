import React from 'react';
import { Database, Bell, Flame, ShieldCheck } from 'lucide-react';

export default function StatsSummary({ stats, mockMode }) {
  return (
    <section className="stats-container animate-slide-up">
      {/* Total Processed */}
      <div className="stat-card">
        <div className="stat-icon indigo">
          <Database style={{ width: '1.1rem', height: '1.1rem' }} />
        </div>
        <div className="stat-meta">
          <span className="stat-label">Processed</span>
          <span className="stat-value">{stats.total_processed}</span>
        </div>
      </div>

      {/* Important Notifications */}
      <div className="stat-card">
        <div className="stat-icon purple">
          <Bell style={{ width: '1.1rem', height: '1.1rem' }} />
        </div>
        <div className="stat-meta">
          <span className="stat-label">Important</span>
          <span className="stat-value">{stats.important_count}</span>
        </div>
      </div>

      {/* High Priority Alerts */}
      <div className="stat-card">
        <div className="stat-icon rose">
          <Flame style={{ width: '1.1rem', height: '1.1rem' }} />
        </div>
        <div className="stat-meta">
          <span className="stat-label">High Priority</span>
          <span className="stat-value">{stats.high_priority_count}</span>
        </div>
      </div>

      {/* Ingestion Mode */}
      <div className="stat-card">
        <div className="stat-icon emerald">
          <ShieldCheck style={{ width: '1.1rem', height: '1.1rem' }} />
        </div>
        <div className="stat-meta">
          <span className="stat-label">Engine Mode</span>
          <span className="stat-value" style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: '700' }}>
            {mockMode === "false" || mockMode === false ? "LIVE IMAP" : "SIMULATION"}
          </span>
        </div>
      </div>
    </section>
  );
}
