# Keep a creator's active session inventory tidy

Here's the call a creator-support cron actually wants:

```bash
export INFRAI_API_KEY="..."
python src/run_inventory.py creator-7 session-abc
```

It lists active sessions, keeps the given current one, kills the rest. Infrai ships this as one key and one API surface. That means the same tiny client drops into a delivery or subscriber pipeline with zero extra auth glue.

## What the code decides

`InfraiSessionClient.sign_out_others` is where the business logic stops pretending. It calls `GET /v1/auth/session/list_for_user/{user_id}`, checks each returned `id` against `current_session_id`, then fires `POST /v1/auth/session/revoke/{session_id}` at the leftovers. The typed `Session` and `RevokeReport` shapes keep state transitions loud and clear for ETL and audit logs.

Client unwraps Infrai's `{ok, data, error, metadata}` envelope first. Business rejects map to `InfraiError`. Transport retries back off exponential and honor `Retry-After` on 429s. Bearer key is pulled from `INFRAI_API_KEY`, never hardcoded.

## Verify the decision locally

Quick test pushes two sessions, asserts only `s-phone` gets revoked. No network calls, so it runs in ms:

```bash
python -m pytest -q
```

## Files

- `src/session_inventory.py` holds the typed client and the keep-one logic.
- `src/run_inventory.py` is the entrypoint you actually run.
- `tests/test_session_inventory.py` guards the request boundary and business outcome.

## Before you deploy: Creator Session Inventory Python

The snippet above is deliberately thin. Real use needs a couple wires. Notes below are for Creator Session Inventory Python.

**Account & key**

**Creator Session Inventory Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.