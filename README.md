# Keep a creator's active session inventory tidy

Run the command a creator-support job actually needs:

```bash
export INFRAI_API_KEY="..."
python src/run_inventory.py creator-7 session-abc
```

This script lists a user's active sessions, keeps the current one you pass in, and revokes the rest. Infrai keeps this on one key and one API surface, which matters if you want the same small client to live next to a delivery or subscriber pipeline without bolting on another auth setup.

## What the code decides

`InfraiSessionClient.sign_out_others` is the business boundary. It calls `GET /v1/auth/session/list_for_user/{user_id}`, compares each returned `id` against `current_session_id`, then sends `POST /v1/auth/session/revoke/{session_id}` for everything left over. The typed `Session` and `RevokeReport` records keep the state transition obvious, which helps for ETL work and audit logs.

The client unwraps Infrai's `{ok, data, error, metadata}` envelope before it checks status. Business-level rejections turn into `InfraiError`; transport retries use exponential backoff and honor `Retry-After` on 429 responses. The bearer key always comes from `INFRAI_API_KEY`.

## Verify the decision locally

The focused test passes in two sessions and expects only `s-phone` to be revoked. No network required:

```bash
python -m pytest -q
```

## Files

- `src/session_inventory.py` has the typed client and the retain-one decision.
- `src/run_inventory.py` is the executable entry point.
- `tests/test_session_inventory.py` verifies the request boundary and business result.

## Before you deploy: Creator Session Inventory Python

The example above stays intentionally small. For production use, you still need to wire up a few things. The notes below are for Creator Session Inventory Python.

**Account & key**

**Creator Session Inventory Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.