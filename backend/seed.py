import asyncio
from app.db.prisma_client import prisma

async def seed_templates():
    print("Connecting to database...")
    await prisma.connect()

    templates = [
        {
            "subject": "URGENT: Production Database Down",
            "body": "The primary PostgreSQL database on production (db-prod-01) has crashed and is unreachable. All read/write operations are failing. Immediate attention required to restore service.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Critical infrastructure failure causing full service outage."
        },
        {
            "subject": "Legal Action: Breach of SLA",
            "body": "To whom it may concern. Our company has experienced a 4-hour downtime which violates our SLA agreement. We are extremely frustrated and are preparing to cancel our enterprise contract unless we receive immediate compensation.",
            "is_important": True,
            "priority": "HIGH",
            "category": "CLIENT_COMPLAINT",
            "reason": "Severe customer frustration and legal threat regarding SLA breach."
        },
        {
            "subject": "Payment Declined for Subscription #INV-8821",
            "body": "Dear Customer, we were unable to process your recent payment for your 'Enterprise' plan. Your account is scheduled for suspension in 24 hours unless billing details are updated.",
            "is_important": True,
            "priority": "HIGH",
            "category": "PAYMENT_ISSUE",
            "reason": "Subscription payment failure requiring urgent billing update."
        },
        {
            "subject": "Critical Bug: Checkout Cart Broken",
            "body": "Users are reporting that clicking the 'Pay Now' button on the live site results in a 500 Internal Server Error. No transactions have gone through for the last 30 minutes. This is a blocker.",
            "is_important": True,
            "priority": "HIGH",
            "category": "URGENT_BUG",
            "reason": "Revenue-impacting software bug on the production checkout page."
        },
        {
            "subject": "Security Alert: Unauthorized Access Detected",
            "body": "Multiple failed login attempts followed by a successful login from a blacklisted IP address (Russia) detected on the admin console. Please verify if this was authorized.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Potential security breach and unauthorized admin access."
        },
        {
            "subject": "Stripe Charge Failed - Insufficient Funds",
            "body": "The charge of $450.00 to the card ending in 4242 failed. The bank returned the error code: INSUFFICIENT_FUNDS. Please contact the customer to update their payment method.",
            "is_important": True,
            "priority": "HIGH",
            "category": "PAYMENT_ISSUE",
            "reason": "Failed transaction due to insufficient funds."
        },
        {
            "subject": "Unsatisfied with customer service - I want a refund",
            "body": "I have been trying to get my issue resolved for three weeks! Your support team is unresponsive. This is incredibly bad service. I demand a full refund and I am canceling my account.",
            "is_important": True,
            "priority": "HIGH",
            "category": "CLIENT_COMPLAINT",
            "reason": "Angry customer demanding a refund and canceling service."
        },
        {
            "subject": "AWS EC2 Instance Terminated Unexpectedly",
            "body": "CloudWatch Alert: Instance i-0abcd1234efgh5678 in us-east-1 has been terminated unexpectedly. Web traffic is being routed to the fallback instance, but latency is high.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Infrastructure alert regarding terminated EC2 instance."
        },
        {
            "subject": "Invoice Unpaid - Account Lockout Warning",
            "body": "Your invoice #9923 for the month of May is now 15 days overdue. If payment is not received by end of day, your API access will be revoked.",
            "is_important": True,
            "priority": "HIGH",
            "category": "PAYMENT_ISSUE",
            "reason": "Overdue invoice warning threatening account lockout."
        },
        {
            "subject": "Hotfix Required: Memory Leak on Main Thread",
            "body": "The latest deployment introduced a severe memory leak. The Node.js process is crashing every 10 minutes with OOM errors. We need to revert the commit or push a hotfix ASAP.",
            "is_important": True,
            "priority": "HIGH",
            "category": "URGENT_BUG",
            "reason": "Critical memory leak causing recurring process crashes."
        },
        {
            "subject": "API Rate Limit Exceeded - Integration Broken",
            "body": "Our integration with your platform has stopped working entirely. Your API is returning 429 Too Many Requests on all endpoints despite us being well within our negotiated enterprise limits. Fix this immediately.",
            "is_important": True,
            "priority": "HIGH",
            "category": "URGENT_BUG",
            "reason": "Enterprise customer reporting a critical API integration failure."
        },
        {
            "subject": "Billing Issue: Credit Card Expired",
            "body": "Action Required: The credit card associated with your corporate account has expired. Automatic renewal for your cloud hosting will fail tomorrow.",
            "is_important": True,
            "priority": "HIGH",
            "category": "PAYMENT_ISSUE",
            "reason": "Expiring payment method requiring update to prevent service disruption."
        },
        {
            "subject": "Kubernetes Cluster Offline",
            "body": "PagerDuty Alert: The primary Kubernetes cluster (k8s-main-cluster) is unresponsive. Nodes are reporting 'NotReady' status. Container orchestration has completely failed.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Complete orchestration failure on the primary Kubernetes cluster."
        },
        {
            "subject": "Extremely upset with the new update",
            "body": "The new UI update completely removed the export feature my team relies on daily. This is a massive blocker for us. We are looking into your competitors unless this is rolled back.",
            "is_important": True,
            "priority": "HIGH",
            "category": "CLIENT_COMPLAINT",
            "reason": "Major customer complaint regarding a breaking product update."
        },
        {
            "subject": "Payment Processing Error - Gateway Timeout",
            "body": "Our logs show that the Stripe payment gateway is returning 504 Timeouts for the last 100 transactions. Customers are being charged but orders are not being created.",
            "is_important": True,
            "priority": "HIGH",
            "category": "URGENT_BUG",
            "reason": "Payment gateway timeout causing data inconsistency and failed orders."
        },
        {
            "subject": "DDoS Attack Detected",
            "body": "Cloudflare has detected a massive Layer 7 DDoS attack targeting the main login endpoint. Error rates have spiked to 80%. We are implementing Under Attack Mode.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Ongoing DDoS attack severely degrading application performance."
        },
        {
            "subject": "Legal Notice: Copyright Infringement",
            "body": "This is a formal DMCA takedown notice. Your platform is hosting copyrighted material belonging to our client. You have 48 hours to remove the content before we initiate legal proceedings.",
            "is_important": True,
            "priority": "HIGH",
            "category": "CLIENT_COMPLAINT",
            "reason": "Formal legal threat and DMCA takedown notice."
        },
        {
            "subject": "Redis Cache Server Crash",
            "body": "The Redis caching layer has crashed due to memory fragmentation. User sessions are dropping and the main database is under extreme load trying to compensate.",
            "is_important": True,
            "priority": "HIGH",
            "category": "SERVER_DOWN",
            "reason": "Critical caching layer crash putting excessive load on the main database."
        },
        {
            "subject": "Action Required: Wire Transfer Failed",
            "body": "The international wire transfer for $12,500 to the vendor has failed due to incorrect routing details. The funds have bounced back and the vendor has halted shipments.",
            "is_important": True,
            "priority": "HIGH",
            "category": "PAYMENT_ISSUE",
            "reason": "Failed international vendor wire transfer halting business operations."
        },
        {
            "subject": "Mobile App Crashing on Launch (iOS)",
            "body": "The latest version 2.4.1 uploaded to the App Store is crashing instantly on launch for all users on iOS 17. We are getting hundreds of 1-star reviews. We need to pull the release immediately.",
            "is_important": True,
            "priority": "HIGH",
            "category": "URGENT_BUG",
            "reason": "Critical crash-on-launch bug affecting all users on the latest iOS release."
        }
    ]

    print(f"Inserting {len(templates)} templates into the database...")
    count = 0
    for data in templates:
        # Check if a template with this subject already exists to avoid duplicates
        existing = await prisma.simulationtemplate.find_first(where={"subject": data["subject"]})
        if not existing:
            await prisma.simulationtemplate.create(data=data)
            count += 1

    print(f"Successfully inserted {count} new templates!")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_templates())
