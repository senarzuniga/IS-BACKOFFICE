"""Google Calendar and Gmail integration with graceful fallback."""

from __future__ import annotations

import base64
import os
import pickle
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception:  # pragma: no cover
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None

    class HttpError(Exception):
        pass


class GoogleIntegration:
    """Handle Google Calendar and Gmail operations."""

    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle") -> None:
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.calendar_service = None
        self.gmail_service = None
        self._authenticate()

    def _authenticate(self) -> None:
        if not (Request and Credentials and InstalledAppFlow and build):
            return

        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as token:
                    self.creds = pickle.load(token)
            except Exception:
                self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = None
            else:
                if not os.path.exists(self.credentials_file):
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                except Exception:
                    self.creds = None

            if self.creds:
                try:
                    with open(self.token_file, "wb") as token:
                        pickle.dump(self.creds, token)
                except Exception:
                    pass

        if self.creds:
            try:
                self.calendar_service = build("calendar", "v3", credentials=self.creds)
                self.gmail_service = build("gmail", "v1", credentials=self.creds)
            except Exception:
                self.calendar_service = None
                self.gmail_service = None

    # ============ CALENDAR OPERATIONS ============

    def create_event(
        self,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        location: Optional[str] = None,
    ) -> Dict[str, str]:
        if not self.calendar_service:
            return {"error": "Calendar not authenticated"}

        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Madrid"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Madrid"},
            "attendees": [{"email": email} for email in attendees],
        }
        if location:
            event["location"] = location

        try:
            event_result = self.calendar_service.events().insert(  # type: ignore[union-attr]
                calendarId="primary", body=event, sendUpdates="all"
            ).execute()
            return {
                "id": event_result.get("id", ""),
                "link": event_result.get("htmlLink", ""),
                "status": "created",
            }
        except HttpError as error:
            return {"error": str(error)}

    def get_events(self, days_ahead: int = 30) -> List[Dict]:
        if not self.calendar_service:
            return []

        now = datetime.utcnow().isoformat() + "Z"
        later = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
        try:
            events_result = self.calendar_service.events().list(  # type: ignore[union-attr]
                calendarId="primary",
                timeMin=now,
                timeMax=later,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            return events_result.get("items", [])
        except HttpError:
            return []

    # ============ GMAIL OPERATIONS ============

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        if not self.gmail_service:
            return False

        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        message.attach(MIMEText(body, "plain"))
        if html:
            message.attach(MIMEText(body, "html"))

        try:
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            payload = {"raw": encoded_message}
            self.gmail_service.users().messages().send(userId="me", body=payload).execute()  # type: ignore[union-attr]
            return True
        except HttpError:
            return False

    def get_unread_emails(self, max_results: int = 10) -> List[Dict]:
        if not self.gmail_service:
            return []

        try:
            results = self.gmail_service.users().messages().list(  # type: ignore[union-attr]
                userId="me",
                labelIds=["INBOX"],
                q="is:unread",
                maxResults=max_results,
            ).execute()
            messages = results.get("messages", [])
            emails: List[Dict] = []

            for message in messages:
                msg = self.gmail_service.users().messages().get(userId="me", id=message["id"]).execute()  # type: ignore[union-attr]
                headers = {h.get("name"): h.get("value") for h in msg.get("payload", {}).get("headers", [])}
                emails.append(
                    {
                        "id": message.get("id"),
                        "from": headers.get("From", ""),
                        "subject": headers.get("Subject", ""),
                        "snippet": msg.get("snippet", ""),
                        "received_at": headers.get("Date", ""),
                    }
                )
            return emails
        except HttpError:
            return []


google = GoogleIntegration()
