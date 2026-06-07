"""Mocked tools that agents can call during processing.

These represent external integrations (account lookup, ticketing, notifications).
"""

async def lookup_account_status(user_id: str) -> dict:
    """Mock lookup — returns a deterministic account state."""
    return {"user_id": user_id, "status": "active", "plan": "pro"}


async def create_support_ticket(packet: dict) -> dict:
    """Mock ticket creation: returns a ticket id and link."""
    return {"ticket_id": "TCK-" + packet.get("trace_id", "unknown"), "status": "created"}


async def notify_human(packet: dict) -> dict:
    """Mock notification: pretend to send an email/SLACK message."""
    return {"notified": True, "channel": "email"}
