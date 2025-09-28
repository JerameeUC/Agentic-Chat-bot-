# /intergrations/email/ticket_stub.py
"""
Email / Ticket System Stub.

This module simulates creating a support ticket via email.
It is a placeholder — no actual emails are sent.
"""

from typing import Dict, Any
import datetime
import uuid


class TicketStub:
    """
    A stub ticketing system that generates a fake ticket ID
    and stores basic info in memory.
    """

    def __init__(self):
        self.tickets: Dict[str, Dict[str, Any]] = {}

    def create_ticket(self, subject: str, body: str, user: str | None = None) -> Dict[str, Any]:
        """
        Create a fake support ticket.
        Returns a dictionary with ticket metadata.
        """
        ticket_id = str(uuid.uuid4())
        ticket = {
            "id": ticket_id,
            "subject": subject,
            "body": body,
            "user": user or "anonymous",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "status": "open",
        }
        self.tickets[ticket_id] = ticket
        return ticket

    def get_ticket(self, ticket_id: str) -> Dict[str, Any] | None:
        """Retrieve a ticket by ID if it exists."""
        return self.tickets.get(ticket_id)

    def list_tickets(self) -> list[Dict[str, Any]]:
        """Return all created tickets."""
        return list(self.tickets.values())


# Singleton for convenience
stub = TicketStub()


def create_ticket(subject: str, body: str, user: str | None = None) -> Dict[str, Any]:
    """
    Module-level shortcut.
    """
    return stub.create_ticket(subject, body, user)
