# InboxRadar AI 📡 — Intelligent Email Classification Agent

Welcome to **InboxRadar AI**, an autonomous email categorization assistant and real-time dashboard designed for operations and engineering teams. 

InboxRadar monitors your connected inbox (or simulates it using structured mock scenarios), analyzes the content of incoming emails using **Gemini AI**, decides if they are critical, and instantly pushes warnings to a desktop dashboard using WebSockets and browser notifications.

---

## 🛠️ The Tech Stack

- **Backend**: FastAPI (Python) — Fast, asynchronous, and well-structured API.
- **Frontend**: Next.js (React) — A modern dark-mode dashboard styled with a custom glassmorphism design system.
- **Database**: Supabase (PostgreSQL) — For storing processed email metadata and ensuring duplicate prevention.
- **AI Engine**: Gemini 1.5 Flash API — High-speed cognitive analysis with a robust keyword-based regex classifier fallback.
- **Real-Time Interface**: WebSockets (native) + HTML5 Browser Notifications API.

---

## 🚀 Getting Started

You can spin up the entire system (backend, frontend, database hook, and poller worker) in under two minutes.

### Method 1: The Docker Way (Recommended)

Make sure you have Docker and Docker Compose installed, then execute:

```bash
docker compose up --build
```

- **Dashboard Panel**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

*Note: Environment settings will be loaded automatically from the `.env` file in the root.*

### Method 2: Manual Local Development

If you want to run the components independently on your machine:

#### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 2. Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 🧠 How the AI Classification Works

The heart of the system is the classifier in `backend/app/services/ai.py`.

1. **Gemini Ingestion**: If `GEMINI_API_KEY` is present in your `.env` file, the backend sends the email body to `gemini-1.5-flash` with a strict JSON format prompt.
2. **Rule-Based Fallback**: If the Gemini API key is missing or fails (due to rate limits or network hiccups), the backend seamlessly falls back to a regex-based keyword scanner. This scans for:
   - **Infrastructure keywords** (`down`, `offline`, `unreachable`) &rarr; Category: `SERVER_DOWN`, Priority: `HIGH`.
   - **Billing issues** (`payment failed`, `unpaid`, `insufficient funds`) &rarr; Category: `PAYMENT_ISSUE`, Priority: `HIGH`.
   - **Code/website errors** (`checkout broken`, `bug`, `blocker`) &rarr; Category: `URGENT_BUG`, Priority: `HIGH`.
   - **Transactional receipts** (e.g., standard GitHub invoices paid) &rarr; Category: `BILLING`, Priority: `LOW`, Important: `False`.
   - **General newsletters/Spam** &rarr; Category: `NEWSLETTER` / `SPAM`, Priority: `LOW`, Important: `False`.

This hybrid approach guarantees that the system is **highly available** and works out of the box without any setup keys!

---

## 🎛️ The 3 Ingestion Triggers

InboxRadar provides three ways to test and trigger the classification engine:

1. **Real Inbox Polling (Trigger 1)**:
   The background poller worker connects to your IMAP server (e.g., Gmail) every 2 minutes. It checks for new emails, extracts headers, and processes them.
   - *Duplicate Prevention*: The poller hashes/looks up the email's `Message-ID` in the Supabase PostgreSQL database before running it. A message is **never** processed or displayed twice.

2. **Send Email to Self (Trigger 2)**:
   In the control center on the dashboard, type a Subject and Body and hit "Send SMTP Mail". The backend will send a real email using SMTP TLS to your own connected address. The background poller will automatically grab it on the next sweep (or you can force a scan).

3. **Scenario Simulator (Trigger 3)**:
   Select any mock scenario (e.g., Database Crash, Phishing Spam, Stripe Payment Decline) from the dropdown and click "Simulate Ingestion". The email payload is sent directly to the classifier and database, generating a unique ID so you see the push notification pop up on the dashboard instantly!

---

## 🔔 Instant Push Notifications

When a new critical email is categorized as **Important**:
- A real-time **WebSocket payload** is pushed to all dashboard clients.
- The UI triggers the browser's native **HTML5 Desktop Notification** (even if the tab is running in the background!).
- The dashboard plays a synthesized double-chime tone using the **Web Audio API** (so no external audio file downloads are blocked by browser sandbox security).

---

## ⚠️ Important Considerations & Limitations

- **Gmail App Passwords**: If you connect a real Gmail account, you must generate an **App Password** in your Google Account security settings. Standard Gmail account passwords will be rejected by Google's IMAP/SMTP servers.
- **WebSocket Port Mapping**: If you host this live on a production server, make sure to update the `NEXT_PUBLIC_API_URL` variable in your `.env` so the frontend knows where to direct WebSocket handshake requests.
