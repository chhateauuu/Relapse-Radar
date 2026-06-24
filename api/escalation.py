"""Escalation: build EscalationEvents and send the real SMS via Twilio.   [P3]

The demo's big moment: a real text lands on the sponsor's phone. Twilio creds
live in `.env` (gitignored). With no creds we run in **simulated** mode so the
whole flow still works offline — the EscalationEvent is identical, only the
wire-send is skipped.

EscalationEvent schema: ../shared/contracts.md
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from .rules import Decision


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def send_sms(to: str | None, body: str) -> dict[str, Any]:
    """Send an SMS through Twilio if configured, else simulate.

    Returns {"sent": bool, "simulated": bool, "sid": str | None, "error": str | None}.
    Required env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER.
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (sid and token and from_number and to):
        return {"sent": False, "simulated": True, "sid": None, "error": None}

    try:
        from twilio.rest import Client  # imported lazily so the API runs without twilio

        msg = Client(sid, token).messages.create(body=body, from_=from_number, to=to)
        return {"sent": True, "simulated": False, "sid": msg.sid, "error": None}
    except Exception as exc:  # pragma: no cover - network/credentials dependent
        return {"sent": False, "simulated": True, "sid": None, "error": str(exc)}


def build_event(user_id: str, day: int, decision: Decision) -> dict[str, Any]:
    """Turn a fired rules Decision into an EscalationEvent (contract shape)."""
    return {
        "user_id": user_id,
        "day": day,
        "type": decision["type"],
        "recipient": decision["recipient"],
        "channel": decision["channel"],
        "message": decision["message"],
        "sent_at": _now_iso(),
    }


def dispatch(user_id: str, day: int, decision: Decision) -> dict[str, Any]:
    """Build the EscalationEvent and actually send it when it's a circle SMS.

    Returns the EscalationEvent augmented with a `delivery` block describing the
    send result (or simulated send). `self_nudge` is an on-device push, so no
    SMS is sent.
    """
    event = build_event(user_id, day, decision)
    if decision["type"] == "notify_circle":
        event["delivery"] = send_sms(decision.get("contact"), decision["message"] or "")
    else:
        event["delivery"] = {"sent": False, "simulated": True, "sid": None, "error": None}
    return event
