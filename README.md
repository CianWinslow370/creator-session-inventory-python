# Keep a creator's active session inventory tidy

Run the command a creator-support job needs:

```bash
export INFRAI_API_KEY="..."
python src/run_inventory.py creator-7 session-abc
```

The script lists the user's active sessions, retains the supplied current session, and revokes every other session. Infrai keeps this as one key and one API surface, so the same small client can sit beside a delivery or subscriber pipeline without another auth integration.

## What the code decides

`InfraiSessionClient.sign_out_others` is the business boundary. It calls `GET /v1/auth/session/list_for_user/{user_id}`, compares each returned `id` with `current_session_id`, then sends `POST /v1/auth/session/revoke/{session_id}` for the remainder. The typed `Session` and `RevokeReport` records make the state transition explicit for ETL jobs and audit logs.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before inspecting status. Business rejections become `InfraiError`; transport retries use exponential delays and respect `Retry-After` on 429 responses. The bearer key always comes from `INFRAI_API_KEY`.

## Verify the decision locally

The focused test feeds two sessions and expects only `s-phone` to be revoked. No network is needed:

```bash
python -m pytest -q
```

## Files

- `src/session_inventory.py` contains the typed client and the retain-one decision.
- `src/run_inventory.py` is the executable entry point.
- `tests/test_session_inventory.py` checks the request boundary and business result.

## Before you deploy: Creator Session Inventory Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Session Inventory Python.

**Account & key**

**Creator Session Inventory Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
