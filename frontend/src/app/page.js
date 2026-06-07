"use client";

import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import StatsSummary from '../components/StatsSummary';
import SidebarFilters from '../components/SidebarFilters';
import EmailFeed from '../components/EmailFeed';
import EmailInspector from '../components/EmailInspector';
import SandboxControls from '../components/SandboxControls';

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
  
  // Filtering & Search
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
  let rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  try {
    const urlObj = new URL(rawApiUrl);
    if (urlObj.pathname === '/' || urlObj.pathname === '') {
      rawApiUrl = `${urlObj.origin}/api`;
    }
  } catch (e) {
    // Fallback if not a parseable URL
  }
  const API_URL = rawApiUrl;

  // Authentication Token Logic
  // 1. Check process.env (passed during build or dev)
  // 2. Fallback to a pre-shared 'dev-token' that the backend now recognizes to ensure it works "out of the box"
  const token = process.env.NEXT_PUBLIC_API_TOKEN || 'inboxradar-dev-token-default';
  
  const WS_URL = API_URL.replace('/api', '').replace('http://', 'ws://').replace('https://', 'wss://') + '/ws' + (token ? `?token=${token}` : '');

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

  // Helper function to query backend with pre-shared JWT Token
  const fetchWithAuth = async (url, options = {}) => {
    const headers = {
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (options.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(url, { ...options, headers });
  };

  // Fetch initial API data
  const fetchData = async () => {
    try {
      const emailsRes = await fetchWithAuth(`${API_URL}/emails`);
      if (emailsRes.ok) {
        const emailsData = await emailsRes.json();
        setEmails(emailsData);
      }
      
      const statsRes = await fetchWithAuth(`${API_URL}/emails/stats`);
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      const mockRes = await fetchWithAuth(`${API_URL}/emails/mock-dataset`);
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
      const res = await fetchWithAuth(`${API_URL}/emails/trigger-scan`, { method: 'POST' });
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
      const res = await fetchWithAuth(`${API_URL}/emails/simulate`, {
        method: 'POST',
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
      const res = await fetchWithAuth(`${API_URL}/emails/send-test`, {
        method: 'POST',
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
      <Navbar 
        wsStatus={wsStatus}
        notificationsEnabled={notificationsEnabled}
        bellRinging={bellRinging}
        onRequestNotifications={requestNotificationPermission}
        onTriggerScan={triggerScan}
        polling={polling}
      />

      {/* 2. Stats Summary Grid */}
      <StatsSummary 
        stats={stats}
        mockMode={process.env.NEXT_PUBLIC_MOCK_MODE}
      />

      {/* 3. Main Split Grid */}
      <div className="content-grid">
        
        {/* Column 1: Left Sidebar controls */}
        <SidebarFilters 
          stats={stats}
          showImportantOnly={showImportantOnly}
          setShowImportantOnly={setShowImportantOnly}
          filterPriority={filterPriority}
          setFilterPriority={setFilterPriority}
          filterCategory={filterCategory}
          setFilterCategory={setFilterCategory}
          uniqueCategories={uniqueCategories}
          consoleLogs={consoleLogs}
        />

        {/* Column 2: Center Stream Panel */}
        <EmailFeed 
          filteredEmails={filteredEmails}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedEmail={selectedEmail}
          onSelectEmail={setSelectedEmail}
        />

        {/* Column 3: Dual-State Panel (Inspector OR Sandbox Controls) */}
        <section className="right-panel animate-slide-up">
          {selectedEmail ? (
            <EmailInspector 
              selectedEmail={selectedEmail}
              onClose={() => setSelectedEmail(null)}
            />
          ) : (
            <SandboxControls 
              mockDataset={mockDataset}
              selectedMockId={selectedMockId}
              setSelectedMockId={setSelectedMockId}
              onSimulateMock={simulateMock}
              smtpSubject={smtpSubject}
              setSmtpSubject={setSmtpSubject}
              smtpBody={smtpBody}
              setSmtpBody={setSmtpBody}
              onSendTestSmtp={sendTestSmtp}
            />
          )}
        </section>

      </div>
    </div>
  );
}
