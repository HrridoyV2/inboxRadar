"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, 
  Send, 
  RefreshCw, 
  Database, 
  Sparkles, 
  Mail, 
  Search, 
  Terminal, 
  Flame,
  Clock,
  ShieldCheck,
  FileCode,
  ArrowRight
} from 'lucide-react';

export default function Home() {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState({
    total_processed: 0,
    important_count: 0,
    unimportant_count: 0,
    high_priority_count: 0,
    medium_priority_count: 0,
    low_priority_count: 0
  });
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [mockDataset, setMockDataset] = useState([]);
  const [selectedMockId, setSelectedMockId] = useState('');
  const [smtpSubject, setSmtpSubject] = useState('');
  const [smtpBody, setSmtpBody] = useState('');
  
  // Filtering & Search - default to false so all simulated/custom emails show up immediately
  const [showImportantOnly, setShowImportantOnly] = useState(false);
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Statuses
  const [polling, setPolling] = useState(false);
  const [wsStatus, setWsStatus] = useState('connecting');
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [bellRinging, setBellRinging] = useState(false);
  
  // Console log entries
  const [consoleLogs, setConsoleLogs] = useState([]);
  
  const wsRef = useRef(null);

  // Configuration URLs
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  const WS_URL = API_URL.replace('/api', '').replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';

  // Helper to add log entries
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setConsoleLogs(prev => [{ timestamp, message, type }, ...prev].slice(0, 50));
  };

  // Dynamically synthesize tone using Web Audio API
  const playNotificationSound = () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, ctx.currentTime);
      gain1.gain.setValueAtTime(0, ctx.currentTime);
      gain1.gain.linearRampToValueAtTime(0.12, ctx.currentTime + 0.05);
      gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
      
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(880.00, ctx.currentTime + 0.12);
      gain2.gain.setValueAtTime(0, ctx.currentTime + 0.12);
      gain2.gain.linearRampToValueAtTime(0.12, ctx.currentTime + 0.17);
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);

      osc1.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.5);
      osc2.start(ctx.currentTime + 0.12);
      osc2.stop(ctx.currentTime + 0.7);
    } catch (e) {
      console.warn("Audio Context blocked or failed:", e);
    }
  };

  // Fetch initial API data
  const fetchData = async () => {
    try {
      const emailsRes = await fetch(`${API_URL}/emails`);
      if (emailsRes.ok) {
        const emailsData = await emailsRes.json();
        setEmails(emailsData);
      }
      
      const statsRes = await fetch(`${API_URL}/emails/stats`);
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      const mockRes = await fetch(`${API_URL}/emails/mock-dataset`);
      if (mockRes.ok) {
        const mockData = await mockRes.json();
        setMockDataset(mockData);
        if (mockData.length > 0) setSelectedMockId(mockData[0].id);
      }
    } catch (err) {
      addLog("Failed to sync database. Connection offline.", "error");
    }
  };

  // Request browser notifications permission
  const requestNotificationPermission = async () => {
    if (!("Notification" in window)) {
      addLog("Notifications not supported in this browser.", "warning");
      return;
    }
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      setNotificationsEnabled(true);
      addLog("Desktop push notifications enabled.", "success");
      new Notification("InboxRadar AI Activated", {
        body: "You will receive immediate desktop alerts for important incoming mail.",
        tag: "activation"
      });
    } else {
      setNotificationsEnabled(false);
      addLog("Desktop notifications permission denied.", "warning");
    }
  };

  const triggerPushNotification = (emailRecord) => {
    if (Notification.permission === "granted") {
      new Notification(`[${emailRecord.priority}] ${emailRecord.category}`, {
        body: `From: ${emailRecord.sender}\nSubject: ${emailRecord.subject}\nReason: ${emailRecord.reason}`,
        tag: emailRecord.id,
        requireInteraction: true
      });
    }
  };

  // Trigger manual IMAP Scan (Trigger 1)
  const triggerScan = async () => {
    setPolling(true);
    addLog("Scanning inbox...", "info");
    try {
      const res = await fetch(`${API_URL}/emails/trigger-scan`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        addLog(`Scan complete (${data.mode}). Processed ${data.processed_new_emails} new emails.`, "success");
        fetchData();
      } else {
        addLog("Manual inbox scan failed.", "error");
      }
    } catch (err) {
      addLog("Network connection error during scan.", "error");
    } finally {
      setPolling(false);
    }
  };

  // Simulate Ingestion (Trigger 3)
  const simulateMock = async () => {
    const mockEmail = mockDataset.find(e => e.id === selectedMockId);
    if (!mockEmail) {
      addLog("Select a valid mock scenario first.", "warning");
      return;
    }
    
    addLog(`Simulating scenario: "${mockEmail.subject}"...`, "info");
    try {
      const res = await fetch(`${API_URL}/emails/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender: mockEmail.sender,
          subject: mockEmail.subject,
          body: mockEmail.body
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === "sent_via_smtp") {
          addLog("Mock scenario sent via SMTP! Scanning inbox in 3 seconds...", "success");
          setTimeout(triggerScan, 3000);
        } else {
          addLog("Mock scenario injected and saved.", "success");
        }
        fetchData();
      } else {
        addLog("Failed to process simulated scenario.", "error");
      }
    } catch (err) {
      addLog("Network timeout during mock simulation.", "error");
    }
  };

  // Dispatch SMTP test mail (Trigger 2)
  const sendTestSmtp = async (e) => {
    e.preventDefault();
    if (!smtpSubject || !smtpBody) {
      addLog("Subject and message body are required.", "warning");
      return;
    }

    addLog(`Dispatching test mail: "${smtpSubject}"...`, "info");
    try {
      const res = await fetch(`${API_URL}/emails/send-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: smtpSubject,
          body: smtpBody
        })
      });

      if (res.ok) {
        if (process.env.NEXT_PUBLIC_MOCK_MODE === "false") {
          addLog("Test email sent via SMTP! Scanning inbox in 3 seconds...", "success");
          setTimeout(triggerScan, 3000);
        } else {
          addLog("Test email dispatched and classified successfully!", "success");
        }
        setSmtpSubject('');
        setSmtpBody('');
        // Sync layout data
        fetchData();
      } else {
        const errData = await res.json();
        addLog(`SMTP deliverability error: ${errData.detail || "Server Error"}`, "error");
      }
    } catch (err) {
      addLog("Network connection failure during SMTP request.", "error");
    }
  };

  useEffect(() => {
    fetchData();
    addLog("System initialized. Awaiting ingestion events...", "info");

    if ("Notification" in window) {
      setNotificationsEnabled(Notification.permission === "granted");
    }

    // Connect WebSocket
    const connectWS = () => {
      addLog("Connecting WebSocket channel...", "info");
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        setWsStatus('connected');
        addLog("Real-time WebSocket connection established.", "success");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "NEW_EMAIL") {
            const newEmail = data.email;
            
            // Trigger bell ring animation
            setBellRinging(true);
            setTimeout(() => setBellRinging(false), 1200);
            
            addLog(`New email processed from ${newEmail.sender}`, "alert");
            
            // Push email and update stats
            setEmails(prev => [newEmail, ...prev]);
            setStats(prev => {
              const updated = { ...prev };
              updated.total_processed += 1;
              if (newEmail.is_important) {
                updated.important_count += 1;
                if (newEmail.priority === "HIGH") updated.high_priority_count += 1;
                if (newEmail.priority === "MEDIUM") updated.medium_priority_count += 1;
                if (newEmail.priority === "LOW") updated.low_priority_count += 1;
              } else {
                updated.unimportant_count += 1;
              }
              return updated;
            });

            // Chime & Alert if important
            if (newEmail.is_important) {
              playNotificationSound();
              triggerPushNotification(newEmail);
            }
          }
        } catch (e) {
          console.error("Payload parse error:", e);
        }
      };

      socket.onclose = () => {
        setWsStatus('disconnected');
        addLog("WebSocket link broken. Reconnecting...", "warning");
        setTimeout(connectWS, 4000);
      };

      socket.onerror = (err) => {
        setWsStatus('disconnected');
        console.error("WS connection failure:", err);
      };
    };

    connectWS();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const filteredEmails = emails.filter(email => {
    if (showImportantOnly && !email.is_important) return false;
    if (filterPriority !== 'ALL' && email.priority !== filterPriority) return false;
    if (filterCategory !== 'ALL' && email.category !== filterCategory) return false;
    
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        email.sender.toLowerCase().includes(q) ||
        (email.subject || "").toLowerCase().includes(q) ||
        (email.reason || "").toLowerCase().includes(q) ||
        (email.body || "").toLowerCase().includes(q)
      );
    }
    return true;
  });

  const uniqueCategories = ['ALL', ...new Set(emails.map(e => e.category).filter(Boolean))];

  return (
    <div className="app-container animate-fade-in">
      
      {/* 1. Header Navbar */}
      <header className="navbar">
        <div className="navbar-brand">
          <div className="brand-icon-wrapper">
            <Sparkles style={{ width: '1.1rem', height: '1.1rem', color: '#fff' }} />
            <div className="brand-glow-dot"></div>
          </div>
          <div>
            <h1 className="brand-title">InboxRadar<span className="text-gradient ml-1">AI</span></h1>
            <p className="brand-subtitle">Autonomous Email Reading & Classification Agent</p>
          </div>
        </div>

        <div className="navbar-actions">
          <div className="badge badge-neutral">
            <span style={{ 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              background: wsStatus === 'connected' ? '#10b981' : '#f59e0b',
              marginRight: '4px'
            }}></span>
            WS: {wsStatus}
          </div>

          <button 
            onClick={requestNotificationPermission} 
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
            onClick={triggerScan}
            className="btn-primary"
            style={{ fontSize: '0.725rem', padding: '0.45rem 0.875rem' }}
          >
            <RefreshCw className={polling ? 'animate-spin' : ''} style={{ width: '0.8rem', height: '0.8rem' }} />
            Scan Inbox
          </button>
        </div>
      </header>

      {/* 2. Stats Rows */}
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
              {process.env.NEXT_PUBLIC_MOCK_MODE === "false" ? "LIVE IMAP" : "SIMULATION"}
            </span>
          </div>
        </div>
      </section>

      {/* 3. Main Split Grid */}
      <div className="content-grid">
        
        {/* Column 1: Left Sidebar controls */}
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

        {/* Column 2: Center Stream Panel */}
        <main className="stream-panel animate-slide-up">
          <div className="feed-header-row">
            <div>
              <h2 className="feed-title">Alerts & Incoming Feed</h2>
              <p className="feed-subtitle">
                Showing {filteredEmails.length} email{filteredEmails.length !== 1 ? 's' : ''}
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
              />
            </div>
          </div>

          <div className="cards-feed-stream">
            {filteredEmails.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#475569' }}>
                <Mail style={{ width: '2rem', height: '2rem', margin: '0 auto 0.75rem', display: 'block', opacity: '0.3' }} />
                <h3 style={{ fontSize: '0.8rem', fontWeight: '600', color: '#94a3b8' }}>No emails match filters</h3>
                <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: '4px' }}>
                  Try resetting filters or submitting a simulated email.
                </p>
              </div>
            ) : (
              filteredEmails.map(email => (
                <div 
                  key={email.id} 
                  onClick={() => setSelectedEmail(email)}
                  className="alert-card"
                  style={{
                    borderColor: selectedEmail && selectedEmail.id === email.id ? '#4f46e5' : 'rgba(255, 255, 255, 0.05)',
                    background: selectedEmail && selectedEmail.id === email.id ? 'rgba(79, 70, 229, 0.06)' : 'rgba(16, 21, 38, 0.4)'
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
                        <span style={{ color: '#ffffff' }}>{email.sender}</span>
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
              ))
            )}
          </div>
        </main>

        {/* Column 3: Dual-State Panel (Inspector OR Sandbox Sandbox) */}
        <section className="right-panel animate-slide-up">
          {selectedEmail ? (
            /* State B: Email detailed inspector */
            <div className="inspector-details">
              <div className="right-panel-header">
                <h2 className="right-panel-title">
                  <Mail style={{ width: '1rem', height: '1rem', color: '#818cf8' }} />
                  Email Inspector
                </h2>
                <button 
                  onClick={() => setSelectedEmail(null)} 
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
          ) : (
            /* State A: Sandbox Sandbox */
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
                        [{item.expected_priority}] {item.subject}
                      </option>
                    ))}
                  </select>
                </div>

                <button 
                  onClick={simulateMock} 
                  className="btn-primary"
                  style={{ width: '100%' }}
                >
                  Trigger Simulation
                  <ArrowRight style={{ width: '0.8rem', height: '0.8rem' }} />
                </button>
              </div>

              {/* Trigger 2: SMTP Sender */}
              <form onSubmit={sendTestSmtp} className="control-section">
                <h3 className="control-section-header">
                  <Send style={{ width: '0.875rem', height: '0.875rem', color: '#6366f1' }} />
                  SMTP Send Test (Trigger 2)
                </h3>
                <p style={{ fontSize: '0.725rem', color: '#64748b', margin: '0.25rem 0' }}>
                  Simulates sending a custom email to self. Processed instantly.
                </p>

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
          )}
        </section>

      </div>

      {/* Footer */}
      <footer className="footer-text">
        <p>&copy; 2026 TQTech Ltd. All rights reserved. Developed for TQTech Automation Suite.</p>
        <p style={{ marginTop: '2px', opacity: 0.6 }}>Built using Next.js, FastAPI, and Supabase. Powered by Gemini Flash 1.5.</p>
      </footer>

    </div>
  );
}
