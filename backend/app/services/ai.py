import json
import re
import logging
from typing import Dict, Any
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini if the API key is provided
if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini API successfully configured.")
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
else:
    logger.warning("No GEMINI_API_KEY found in configuration. Falling back to rules-based classifier.")


def rules_based_classify(sender: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Fallback classifier that uses regex and keyword rules to determine email priority.
    Designed to mimic LLM decisions for testing and high availability.
    """
    subject_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    sender_lower = (sender or "").lower()

    # Default values
    important = False
    priority = "LOW"
    category = "OTHER"
    reason = "Email does not match any high-priority rule and is ignored."

    # 1. Server Outage / Infrastructure Issues
    if any(k in subject_lower or k in body_lower for k in ["offline", "server down", "unreachable", "crash", "outage", "critical", "db-prod", "monitoring"]):
        important = True
        priority = "HIGH"
        category = "SERVER_DOWN"
        reason = "System monitoring flagged a potential server outage or critical hardware infrastructure failure."

    # 2. Client Complaint / SLA Violation
    elif any(k in subject_lower or k in body_lower for k in ["unsatisfied", "frustration", "complain", "cancel contract", "sla", "sla violation", "legal", "bad service"]):
        important = True
        priority = "HIGH"
        category = "CLIENT_COMPLAINT"
        reason = "Detected strong negative sentiment, SLA complaint, or request to terminate services from a customer."

    # 3. Payment Failure / Billing Alert
    elif any(k in subject_lower or k in body_lower for k in ["payment failed", "billing issue", "failed transaction", "insufficient funds", "charge failed", "invoice unpaid", "stripe", "payment declined", "unable to process", "suspension", "billing details"]):
        # Verify it's actually a failure, not a success receipt
        if any(k in subject_lower or k in body_lower for k in ["success", "receipt", "paid", "thank you for your payment"]) and not any(f in body_lower for f in ["fail", "decline", "error"]):
            important = False
            priority = "LOW"
            category = "BILLING"
            reason = "Standard invoice payment confirmation receipt (no action required)."
        else:
            important = True
            priority = "HIGH"
            category = "PAYMENT_ISSUE"
            reason = "A payment failure, transaction decline, or unpaid invoice warning requires immediate financial resolution."

    # 4. Urgent Bugs
    elif any(k in subject_lower or k in body_lower for k in ["bug", "checkout broken", "revert", "hotfix", "broken on prod", "blocker"]):
        important = True
        priority = "HIGH"
        category = "URGENT_BUG"
        reason = "Critical code block or website layout failure reported on the production environment."

    # 5. Spam / Lucky Winner
    elif any(k in subject_lower or k in body_lower for k in ["winner", "win a", "gift card", "lottery", "sweepstakes", "claim your prize", "amazon card"]):
        important = False
        priority = "LOW"
        category = "SPAM"
        reason = "High probability of phishing spam, lottery scan, or unverified cash reward promotion."

    # 6. Newsletter / Tech Digests
    elif any(k in subject_lower or k in body_lower for k in ["newsletter", "weekly", "digest", "bytesize", "tech news", "subscribe"]):
        important = False
        priority = "LOW"
        category = "NEWSLETTER"
        reason = "Periodic technical newsletter or general subscription mailing list (low priority)."

    # 7. Personal Chat
    elif any(k in subject_lower or k in body_lower for k in ["lunch", "coffee", "meeting up", "how are you"]):
        important = False
        priority = "LOW"
        category = "PERSONAL"
        reason = "Casual personal communication or scheduling query (low priority)."

    return {
        "important": important,
        "priority": priority,
        "category": category,
        "reason": reason
    }


def classify_email(sender: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Classifies an email using Gemini API.
    Raises an exception if the API call fails or key is missing.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API key is missing. Please configure GEMINI_API_KEY to process emails.")

    prompt = f"""
You are an expert AI email classification assistant. Analyze the incoming email below and determine its importance, priority level, category, and justification.

Sender: {sender}
Subject: {subject}
Body:
{body}

CLASSIFICATION RULES:
- Important (important = true):
  * Client complaints, SLA violations, legal issues, or customer frustration emails.
  * Payment failures, unpaid invoices, billing card declines, or critical checkout failures.
  * Server offline alerts, system downtime reports, security breaches, or data crash logs.
- Unimportant (important = false):
  * Normal successful transaction receipts (e.g., "Your card was charged successfully", "GitHub invoice paid") where no customer action is needed.
  * SPAM, promotional offers, lottery winnings, and unverified gift cards.
  * Newsletters, developer digests, blogs, and marketing materials.
  * Non-urgent personal chats, catch-ups, or casual scheduling.

CATEGORIES:
Use one of these specific uppercase strings: "PAYMENT_ISSUE", "SERVER_DOWN", "CLIENT_COMPLAINT", "URGENT_BUG", "SPAM", "NEWSLETTER", "BILLING", "PERSONAL", "OTHER".

PRIORITIES:
Use one of these: "HIGH", "MEDIUM", "LOW". High importance should map to "HIGH".

Return your answer strictly as a JSON object with this format, using double quotes for strings and standard boolean values (no extra markdown formatting outside JSON):
{{
  "important": true|false,
  "priority": "HIGH"|"MEDIUM"|"LOW",
  "category": "CATEGORY_NAME",
  "reason": "A single clear, professional sentence justifying this decision."
}}
"""

    try:
        # Use gemini-pro (Gemini 1.0) which is universally available across all regions and keys
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        
        # Clean potential markdown formatting from Gemini 1.0 Pro output
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        
        # Verify response keys exist and values are valid
        if "important" in data and "priority" in data and "category" in data and "reason" in data:
            # Ensure priority and category are formatted correctly
            data["priority"] = str(data["priority"]).upper()
            data["category"] = str(data["category"]).upper()
            
            # Robust boolean conversion for 'important' (handles strings "true"/"false")
            if isinstance(data["important"], str):
                data["important"] = data["important"].lower() == "true"
            else:
                data["important"] = bool(data["important"])
                
            return data
        else:
            raise ValueError(f"Gemini returned missing keys: {response.text}")
            
    except Exception as e:
        logger.error(f"Gemini classification failed: {e}")
        raise ValueError(f"Gemini AI classification failed: {str(e)}")
