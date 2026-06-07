import React from 'react';
import { Terminal } from 'lucide-react';

export default function SidebarFilters({
  stats,
  showImportantOnly,
  setShowImportantOnly,
  filterPriority,
  setFilterPriority,
  filterCategory,
  setFilterCategory,
  uniqueCategories,
  consoleLogs
}) {
  return (
    <aside className="sidebar-col animate-slide-up">
      {/* Stream Filtering Options */}
      <div className="sidebar-widget">
        <h3 className="widget-title">Importance Filter</h3>
        <div className="filter-group-list">
          <button 
            onClick={() => setShowImportantOnly(false)} 
            className={`filter-item-btn ${!showImportantOnly ? 'active' : ''}`}
          >
            <span>All Processed</span>
            <span className="filter-count-badge">{stats.total_processed}</span>
          </button>
          <button 
            onClick={() => setShowImportantOnly(true)} 
            className={`filter-item-btn ${showImportantOnly ? 'active' : ''}`}
          >
            <span>Important Alerts</span>
            <span className="filter-count-badge">{stats.important_count}</span>
          </button>
        </div>
      </div>

      <div className="sidebar-widget">
        <h3 className="widget-title">Priority Levels</h3>
        <div className="filter-group-list">
          <button 
            onClick={() => setFilterPriority('ALL')} 
            className={`filter-item-btn ${filterPriority === 'ALL' ? 'active' : ''}`}
          >
            <span>All Priorities</span>
          </button>
          <button 
            onClick={() => setFilterPriority('HIGH')} 
            className={`filter-item-btn ${filterPriority === 'HIGH' ? 'active' : ''}`}
          >
            <span>High</span>
            <span className="filter-count-badge">{stats.high_priority_count}</span>
          </button>
          <button 
            onClick={() => setFilterPriority('MEDIUM')} 
            className={`filter-item-btn ${filterPriority === 'MEDIUM' ? 'active' : ''}`}
          >
            <span>Medium</span>
            <span className="filter-count-badge">{stats.medium_priority_count}</span>
          </button>
          <button 
            onClick={() => setFilterPriority('LOW')} 
            className={`filter-item-btn ${filterPriority === 'LOW' ? 'active' : ''}`}
          >
            <span>Low</span>
            <span className="filter-count-badge">{stats.low_priority_count}</span>
          </button>
        </div>
      </div>

      <div className="sidebar-widget">
        <h3 className="widget-title">Categories</h3>
        <div className="filter-group-list" style={{ maxHeight: '160px', overflowY: 'auto', paddingRight: '2px' }}>
          {uniqueCategories.map(cat => (
            <button 
              key={cat} 
              onClick={() => setFilterCategory(cat)} 
              className={`filter-item-btn ${filterCategory === cat ? 'active' : ''}`}
              style={{ textTransform: 'capitalize' }}
            >
              <span>{cat.toLowerCase().replace('_', ' ')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Console Logger Widget */}
      <div className="sidebar-widget log-console">
        <h3 className="widget-title">
          <Terminal style={{ width: '0.8rem', height: '0.8rem' }} />
          Live System Logs
        </h3>
        <div className="console-box">
          {consoleLogs.length === 0 ? (
            <p style={{ color: '#334155', fontStyle: 'italic' }}>Awaiting events...</p>
          ) : (
            consoleLogs.map((log, index) => (
              <div key={index} className="console-line">
                <span className="console-time">[{log.timestamp}]</span>
                <span style={{
                  color: log.type === 'success' ? '#10b981' :
                         log.type === 'error' ? '#f43f5e' :
                         log.type === 'warning' ? '#fbbf24' :
                         log.type === 'alert' ? '#818cf8' : '#e2e8f0',
                  fontWeight: log.type === 'alert' ? '600' : 'normal'
                }}>
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
