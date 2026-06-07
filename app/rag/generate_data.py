"""Generate synthetic support docs and tickets for the RAG corpus.

Outputs:
- data/docs.json (list of docs)
- data/tickets.json (list of tickets)

This is quick and idempotent for demos.
"""
import json
import os
from uuid import uuid4

OUT_DIR = os.getenv(
    "RAG_DATA_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")),
)

OUT_DIR = os.path.abspath(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

markdowns = {1: """# Introduction to CloudFlow
                    Welcome to CloudFlow v2.3.1 — your workflow automation platform.  
                    This guide explains the basics: creating your first workflow, connecting apps, and monitoring execution.

                    ---

                    # Installing CloudFlow Desktop Agent
                    CloudFlow requires the Desktop Agent (v1.4.0) for local triggers.  
                    Steps:
                    1. Download from Settings > Downloads.
                    2. Run installer.
                    3. Verify agent status in Dashboard.

                    ---

                    # Creating Your First Workflow
                    1. Navigate to Workflows > New.
                    2. Select a trigger (e.g., "New Email in Gmail").
                    3. Add actions (e.g., "Create Task in Asana").
                    4. Save and test.

                    ---

                    # Understanding Workflow Triggers
                    Triggers are events that start workflows.  
                    Examples:
                    - File uploaded to OneDrive.
                    - New row in Google Sheets.
                    - API webhook received.

                    ---

                    # CloudFlow Dashboard Overview
                    The dashboard shows:
                    - Active workflows.
                    - Execution logs.
                    - Error alerts (codes CF-ERR-101 to CF-ERR-199).
                """,
             2: """# Managing Your CloudFlow Account
                    Update profile, change password, and configure MFA under Settings > Account.

                    ---

                    # Subscription Plans
                    CloudFlow offers:
                    - Free (2 workflows, 500 runs/month).
                    - Pro ($29/month, unlimited workflows).
                    - Enterprise (custom pricing).

                    ---

                    # Updating Payment Method
                    Go to Settings > Billing > Payment Method.  
                    Supported: Visa, MasterCard, PayPal.

                    ---

                    # Viewing Invoices
                    Invoices are downloadable PDFs under Billing > Invoices.  
                    Each invoice includes VAT ID and transaction reference.

                    ---

                    # Cancelling Your Subscription
                    Navigate to Billing > Subscription > Cancel.  
                    Note: Workflows stop immediately after cancellation.
                """,
             3: """# Common Error Codes
                    - CF-ERR-401: Unauthorized API call.
                    - CF-ERR-502: Workflow timeout.
                    - CF-ERR-709: Integration token expired.

                    ---

                    # Workflow Not Triggering
                    Check:
                    1. Trigger app connection.
                    2. Trigger conditions.
                    3. Agent status (if local).

                    ---

                    # Slow Workflow Execution
                    Possible causes:
                    - High API latency.
                    - Large payloads.
                    - Free plan throttling.

                    ---

                    # Integration Token Expired
                    Re-authenticate under Settings > Integrations.  
                    Error code: CF-ERR-709.

                    ---

                    # Desktop Agent Not Running
                    Verify:
                    - Agent v1.4.0 installed.
                    - Service running in Task Manager.
                    - Firewall exceptions allowed.

                    ---

                    # API Rate Limit Exceeded
                    Error CF-ERR-429.  
                    Resolution: Upgrade to Pro plan or reduce workflow frequency.

                    ---

                    # Workflow Execution Failed
                    Check logs for error codes.  
                    Common fixes: re-map fields, validate JSON payloads.

                    ---

                    # Contacting Support
                    Submit a ticket via Help > Support.  
                    Include workflow ID, error code, and timestamp.
                """,
             4: """# CloudFlow REST API Overview
                    Base URL: https://api.cloudflow.io/v2  
                    Authentication: Bearer token.

                    ---

                    # Authentication Guide
                    Generate API keys under Settings > API Keys.  
                    Scopes: workflows:read, workflows:write.

                    ---

                    # Webhooks
                    CloudFlow supports inbound/outbound webhooks.  
                    Example: POST to https://hooks.cloudflow.io/{workflow_id}

                    ---

                    # Rate Limits
                    - Free: 1000 requests/day.
                    - Pro: 50,000 requests/day.
                    - Enterprise: Unlimited.

                    ---

                    # Integrating with Slack
                    Steps:
                    1. Connect Slack under Integrations.
                    2. Authorize workspace.
                    3. Use "Send Slack Message" action.

                    ---

                    # Integrating with Google Sheets
                    Requires OAuth2.  
                    Supported actions: Add Row, Update Row, Read Data.

                    ---

                    # Using CloudFlow with Asana
                    Triggers: New Task, Task Completed.  
                    Actions: Create Task, Update Task.

                    ---

                    # API Error Codes
                    - CF-API-401: Invalid token.
                    - CF-API-403: Insufficient scope.
                    - CF-API-500: Internal server error.
                """,
             5: """# Conditional Logic in Workflows
                    Use IF/ELSE blocks to branch workflow execution.  
                    Example: IF invoice > $1000 THEN notify finance.

                    ---

                    # Parallel Workflow Execution
                    CloudFlow v2.3.1 supports parallel branches.  
                    Limit: 5 concurrent branches per workflow.

                    ---

                    # Workflow Versioning
                    Each workflow has version history.  
                    Rollback available under Workflow > Versions.

                    ---

                    # Audit Logs
                    Enterprise plan includes audit logs.  
                    Logs track user actions, API calls, and workflow changes.
                """
            }

def make_docs():
    docs = []
    for i in range(1, 6):
        docs.append({
            "id": f"doc-{i}",
            "title": f"Getting started guide part {i}",
            "content": markdowns[i],
            "source": "synthetic",
        })
    return docs


def make_tickets():
    tickets = [
                {
                    "id": "TCK-001",
                    "customer_question": "My workflow isn't triggering when a new email arrives in Gmail.",
                    "intent": "bug",
                    "resolution": "Checked Gmail integration token — expired. Customer re-authenticated under Settings > Integrations. Workflow triggered successfully.",
                    "tags": ["workflow", "gmail", "trigger"],
                    "resolved_at": "2026-05-01T10:23:00"
                },
                {
                    "id": "TCK-002",
                    "customer_question": "Error CF-ERR-502 when running workflow with Google Sheets.",
                    "intent": "bug",
                    "resolution": "Workflow exceeded 30s timeout due to large dataset. Suggested splitting sheet into smaller chunks.",
                    "tags": ["error", "google-sheets", "timeout"],
                    "resolved_at": "2026-05-02T14:11:00"
                },
                {
                    "id": "TCK-003",
                    "customer_question": "How do I upgrade from Free to Pro?",
                    "intent": "billing",
                    "resolution": "Guided customer to Billing > Subscription > Upgrade. Payment processed successfully.",
                    "tags": ["billing", "upgrade", "how_to"],
                    "resolved_at": "2026-05-03T09:45:00"
                },
                {
                    "id": "TCK-004",
                    "customer_question": "Desktop Agent won't start on Windows 11.",
                    "intent": "bug",
                    "resolution": "Agent v1.3.0 incompatible with Windows 11. Customer upgraded to v1.4.0 installer.",
                    "tags": ["desktop-agent", "windows11"],
                    "resolved_at": "2026-05-04T16:20:00"
                },
                {
                    "id": "TCK-005",
                    "customer_question": "Can I integrate CloudFlow with Slack?",
                    "intent": "how_to",
                    "resolution": "Provided step-by-step Slack integration guide. Customer connected workspace successfully.",
                    "tags": ["slack", "integration"],
                    "resolved_at": "2026-05-05T11:00:00"
                },
                {
                    "id": "TCK-006",
                    "customer_question": "My invoice shows wrong VAT ID.",
                    "intent": "billing",
                    "resolution": "Corrected VAT ID in account settings. Issued updated invoice PDF.",
                    "tags": ["billing", "invoice"],
                    "resolved_at": "2026-05-06T13:15:00"
                },
                {
                    "id": "TCK-007",
                    "customer_question": "Error CF-API-401 when calling API.",
                    "intent": "bug",
                    "resolution": "Customer used expired token. Generated new API key under Settings > API Keys.",
                    "tags": ["api", "authentication"],
                    "resolved_at": "2026-05-07T08:40:00"
                },
                {
                    "id": "TCK-008",
                    "customer_question": "How do I set conditional logic in workflows?",
                    "intent": "how_to",
                    "resolution": "Explained IF/ELSE block usage. Provided example workflow template.",
                    "tags": ["workflow", "conditional", "how_to"],
                    "resolved_at": "2026-05-08T12:10:00"
                },
                {
                    "id": "TCK-009",
                    "customer_question": "My account was charged twice this month!",
                    "intent": "complaint",
                    "resolution": "Escalated to billing team. Duplicate charge refunded within 48 hours.",
                    "tags": ["billing", "refund", "complaint"],
                    "resolved_at": "2026-05-09T15:30:00"
                },
                {
                    "id": "TCK-010",
                    "customer_question": "Workflow execution failed with CF-ERR-429.",
                    "intent": "bug",
                    "resolution": "Customer exceeded API rate limit. Suggested upgrading to Pro plan.",
                    "tags": ["workflow", "rate-limit"],
                    "resolved_at": "2026-05-10T17:00:00"
                },
                {
                    "id": "TCK-011",
                    "customer_question": "Can I rollback workflow to previous version?",
                    "intent": "how_to",
                    "resolution": "Yes, under Workflow > Versions. Customer rolled back successfully.",
                    "tags": ["workflow", "versioning"],
                    "resolved_at": "2026-05-11T09:00:00"
                },
                {
                    "id": "TCK-012",
                    "customer_question": "My workflow is running very slowly.",
                    "intent": "bug",
                    "resolution": "Identified inefficient loop in workflow. Suggested optimization and provided example.",
                    "tags": ["workflow", "performance"],
                    "resolved_at": "2026-05-12T14:45:00"
                }
            ]

    return tickets


if __name__ == "__main__":
    docs = make_docs()
    tickets = make_tickets()
    with open(os.path.join(OUT_DIR, "docs.json"), "w", encoding="utf8") as f:
        json.dump(docs, f, indent=2)
    with open(os.path.join(OUT_DIR, "tickets.json"), "w", encoding="utf8") as f:
        json.dump(tickets, f, indent=2)
    print("Wrote docs.json and tickets.json to", OUT_DIR)
