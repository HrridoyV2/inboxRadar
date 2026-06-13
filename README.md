# InboxRadar AI 📡 — Intelligent Email Classification Agent

Welcome to **InboxRadar AI**, an autonomous email categorization assistant and real-time dashboard designed for operations and engineering teams. 

> [!TIP]
> **🌟 Live Demo Links:**
> - **Frontend Dashboard**: [https://inboxradar.mutho.tech](https://inboxradar.mutho.tech)
> - **Backend API**: [https://api.inboxradar.mutho.tech](https://api.inboxradar.mutho.tech)
> - **📽️ Loom Video Walkthrough**: [Watch Here](https://www.loom.com/share/b8af9cf0596645cfacfbfdea5fee03dd)

InboxRadar monitors your connected inbox (or simulates it using structured mock scenarios), analyzes the content of incoming emails using **Google Gemini**, decides if they are critical, and instantly pushes warnings to a desktop dashboard using WebSockets and browser notifications.

---

## 🛠️ The Tech Stack

- **Backend**: FastAPI (Python) — Fast, asynchronous, and well-structured API.
- **Frontend**: Next.js (React) — A modern dark-mode dashboard styled with a custom glassmorphism design system.
- **Database**: Supabase (PostgreSQL) — For storing processed email metadata and ensuring duplicate prevention.
- **AI Engine**: Google Gemini (Flash Latest) — High-speed cognitive analysis with strict JSON output parsing for highly accurate classification.
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

1. **Gemini Ingestion**: If `GEMINI_API_KEY` is present in your `.env` file, the backend sends the email body to `gemini-flash-latest` (or newer models depending on your API key) with a strict JSON format prompt.
2. **Strict Error Handling**: If the Gemini API key is missing or fails (due to rate limits or network hiccups), the backend halts processing immediately and bubbles the error up to the UI so you are instantly informed of the problem.

*(Note: There is also a dormant legacy Rules-Based Fallback Engine built-in for local offline development, which relies on regex matching for keywords like "server down", "payment failed", and "urgent bug".)*

---

## 🎛️ The 2 Ingestion Triggers

InboxRadar provides two primary ways to test and trigger the classification engine:

1. **Send Email to Self (Trigger 1)**:
   In the control center on the dashboard, type a Subject and Body and hit "Send Custom Email". The backend will process the payload, classify it using the AI, and you will see it pop up in your feed just like a real email.

2. **Scenario Simulator (Trigger 2)**:
   Select any mock scenario (e.g., Database Crash, Phishing Spam, Stripe Payment Decline) from the dropdown and click "Trigger Simulation". The email payload is sent directly to the classifier and database, generating a unique ID so you see the push notification pop up on the dashboard instantly!

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
