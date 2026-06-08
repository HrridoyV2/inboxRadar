import React from 'react';
import { Search, Mail, Loader2 } from 'lucide-react';
import EmailCard from './EmailCard';

export default function EmailFeed({
  filteredEmails,
  searchQuery,
  setSearchQuery,
  selectedEmail,
  onSelectEmail,
  loading
}) {
  return (
    <main className="stream-panel animate-slide-up">
      <div className="feed-header-row">
        <div>
          <h2 className="feed-title">Alerts & Incoming Feed</h2>
          <p className="feed-subtitle">
            {loading ? 'Refreshing database...' : `Showing ${filteredEmails.length} email${filteredEmails.length !== 1 ? 's' : ''}`}
          </p>
        </div>
      </div>

      <div className="filter-toolbar">
        <div className="search-wrapper">
          <Search className="search-icon" />
          <input 
            type="text" 
            placeholder="Search sender, subject, content..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-control search-input"
            disabled={loading}
          />
        </div>
      </div>

      <div className="cards-feed-stream" style={{ position: 'relative' }}>
        {loading ? (
          <div className="loading-overlay">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            <p className="text-sm font-medium">Syncing database...</p>
          </div>
        ) : filteredEmails.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#475569' }}>
            <Mail style={{ width: '2rem', height: '2rem', margin: '0 auto 0.75rem', display: 'block', opacity: '0.3' }} />
            <h3 style={{ fontSize: '0.8rem', fontWeight: '600', color: '#94a3b8' }}>No emails match filters</h3>
            <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: '4px' }}>
              Try resetting filters or submitting a simulated email.
            </p>
          </div>
        ) : (
          filteredEmails.map(email => (
            <EmailCard 
              key={email.id} 
              email={email} 
              selectedEmail={selectedEmail} 
              onSelect={onSelectEmail} 
            />
          ))
        )}
      </div>
    </main>
  );
}
