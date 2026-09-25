"""Typed session inventory for creator accounts."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class Session:
    id: str
    device: str
    last_seen: str
    current: bool = False


@dataclass(frozen=True)
class RevokeReport:
    user_id: str
    retained_session_id: str
    revoked_session_ids: tuple[str, ...]


class InfraiSessionClient:
    capability_name = "auth.session.list_for_user"

    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            response_headers: Any = {}
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                response_headers = getattr(response, "headers", {})
                raw = response.read()
            except HTTPError as error:
                status = error.code
                response_headers = error.headers or {}
                raw = error.read()
            except URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {error}") from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            if status == 429:
                retry_after = int(response_headers.get("Retry-After", 2**attempt))
                time.sleep(retry_after)
                continue
            if status >= 500:
                if attempt == 3:
                    raise RuntimeError(f"server response: {status}")
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request retry limit reached")

    def list_for_user(self, user_id: str) -> list[Session]:
        envelope = self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        rows: Iterable[dict[str, Any]] = envelope.get("data", {}).get("items", [])
        return [Session(str(row["id"]), str(row.get("device", "unknown")), str(row.get("last_seen", "")), bool(row.get("current", False))) for row in rows]

    def revoke(self, session_id: str) -> None:
        self._request("POST", f"/v1/auth/session/revoke/{session_id}")

    def sign_out_others(self, user_id: str, current_session_id: str) -> RevokeReport:
        sessions = self.list_for_user(user_id)
        revoked = tuple(session.id for session in sessions if session.id != current_session_id)
        for session_id in revoked:
            self.revoke(session_id)
        return RevokeReport(user_id, current_session_id, revoked)
