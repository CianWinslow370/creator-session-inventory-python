import argparse
import json

from session_inventory import InfraiSessionClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep one creator session and sign out the rest")
    parser.add_argument("user_id")
    parser.add_argument("current_session_id")
    args = parser.parse_args()
    report = InfraiSessionClient().sign_out_others(args.user_id, args.current_session_id)
    print(json.dumps({"user_id": report.user_id, "retained_session_id": report.retained_session_id, "revoked_session_ids": report.revoked_session_ids}))


if __name__ == "__main__":
    main()

