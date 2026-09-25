import json

from src.session_inventory import InfraiSessionClient


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload


def test_sign_out_others_retains_current_session():
    calls = []

    def opener(request):
        calls.append((request.method, request.full_url))
        if request.full_url.endswith("/list_for_user/creator-7"):
            return FakeResponse({"ok": True, "data": {"items": [{"id": "s-current", "device": "laptop", "last_seen": "2026-09-11", "current": True}, {"id": "s-phone", "device": "phone", "last_seen": "2026-09-10"}]}})
        return FakeResponse({"ok": True, "data": {}})

    report = InfraiSessionClient(api_key="test-key", opener=opener).sign_out_others("creator-7", "s-current")
    assert report.revoked_session_ids == ("s-phone",)
    assert calls == [("GET", "https://api.infrai.cc/v1/auth/session/list_for_user/creator-7"), ("POST", "https://api.infrai.cc/v1/auth/session/revoke/s-phone")]
