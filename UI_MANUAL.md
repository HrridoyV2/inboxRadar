# InboxRadar AI - User Interface Manual

Welcome to the InboxRadar AI! This guide is designed to help any user navigate and interact with the user interface effectively. The UI is built to be intuitive, allowing you to monitor your categorized emails in real-time and test the system through simulated events.

> [!TIP]
> **🌟 Live Project Links:**
> - **Frontend Dashboard**: [https://inboxradar.mutho.tech](https://inboxradar.mutho.tech)
> - **Backend API**: [https://api.inboxradar.mutho.tech](https://api.inboxradar.mutho.tech)
> - **📽️ Loom Video Walkthrough**: [Watch Here](https://www.loom.com/share/b8af9cf0596645cfacfbfdea5fee03dd)

## 1. Top Navigation Bar (Status & Alerts)

At the very top of the interface, you'll find essential status indicators and quick-action buttons:

*   **WS Connection Status**: Look for the small badge indicating the WebSocket status. A green dot (`WS: connected`) means you are receiving live, real-time updates. An orange dot indicates it's trying to reconnect.
*   **Enable Alerts**: Click the **"Enable Alerts"** button to allow browser push notifications. Once enabled (the button will turn green and say "Alerts Enabled"), you will receive immediate desktop pop-ups whenever a high-priority or important email arrives, even if the app is in the background. You can click it again to toggle them off.
*   **Sync Database**: While the app syncs automatically every 2 minutes and via WebSocket, you can manually pull the latest data anytime by clicking the **"Sync Database"** button.

## 2. Statistics Summary

Just below the navigation bar is a quick overview dashboard. This shows you:
*   **Total Emails Processed**: The lifetime count of emails analyzed by the AI.
*   **Importance Breakdown**: How many emails were flagged as *Important* versus *Unimportant*.
*   **Priority Distribution**: A clear count of High, Medium, and Low priority emails.

## 3. Sidebar Filters (Left Panel)

The left side of the screen is dedicated to helping you quickly find what you're looking for.

*   **Show Important Only**: Toggle this switch to instantly hide all low-value emails and focus only on what matters.
*   **Filter by Priority**: Use the dropdown to isolate emails that are High, Medium, or Low priority.
*   **Filter by Category**: The AI automatically tags emails with categories (e.g., "Urgent", "Billing", "Complaint"). Use this dropdown to filter your view by a specific topic.
*   **System Console**: At the bottom of the sidebar, you'll see a live terminal window. This displays real-time logs, errors, and system activity so you know exactly what the engine is doing behind the scenes.

## 4. Main Email Feed & Search (Center Panel)

The center of the screen is where your actual email stream lives.

*   **Search Bar**: Type any keyword, sender name, or subject to instantly search through all processed emails.
*   **Feed**: Emails appear here sequentially as they are ingested. Each card displays the sender, subject, an AI summary (reason), and color-coded priority badges.
*   **Email Inspector**: Click on any email card in the feed! A detailed pop-up (Modal) will appear showing you the full original email body, alongside the AI's exact reasoning and extracted metrics. 

## 5. Sandbox Controls (Right Panel)

The right panel is your testing environment. It allows you to inject emails into the system to see how the AI reacts.

*   **Sticky Receiving Email**: At the very top, you'll see a highlighted, sticky banner displaying the exact email address the system is currently monitoring.
*   **Simulator Ingest**: Want to see how the AI handles a server crash alert or a billing complaint? Select a pre-configured scenario from the dropdown menu and click **"Trigger Simulation"**. It will instantly hit the AI engine and appear in your feed.
*   **SMTP Send Test**: Want to write your own custom email? Fill out the "Subject" and "Body Content" text boxes, and click **"Send Custom Email"**. The system will process it live, classify it, and you'll see it pop up in your feed just like a real email.

---

### Pro Tips:
*   **Keep it Open**: For the best experience, keep the tab open on a secondary monitor and enable notifications.
*   **Watch the Console**: If a simulation fails or you aren't receiving emails, check the bottom left System Console logs for real-time troubleshooting. 
