#!/usr/bin/env python3
"""Quota-saving supervisor with retry history persisted in recovery PRs.

Never owns research, changes authorization, or waits on a private CI runner.
The existing supervisor supplies state/lease validation and signal creation.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from urllib.parse import urlencode


def next_signal(records, now, timeout_seconds=360, maximum=3):
    """Return (kind, attempt), using durable PR creation times, not RAM."""
    if not records:
        return "request", 1
    if now.tzinfo is None:
        raise ValueError("A timezone-aware clock is required")
    for attempt, created in records:
        if type(attempt) is not int or not 1 <= attempt <= maximum:
            raise ValueError("Invalid durable attempt number")
        if created.tzinfo is None or created > now + timedelta(seconds=120):
            raise ValueError("Invalid durable request timestamp")
    highest = max(attempt for attempt, _ in records)
    # Conservatively wait from the latest duplicate, should one exist.
    created = max(t for attempt, t in records if attempt == highest)
    if (now - created).total_seconds() < timeout_seconds:
        return "wait", highest
    if highest == maximum:
        return "alert", highest
    return "request", highest + 1


def request_history(api, incident, parse_timestamp, maximum=3):
    """Read exact deterministic attempt branches, including closed PRs."""
    records = []
    owner = api.repo.split("/")[0]
    for attempt in range(1, maximum + 1):
        branch = "watchdog-recovery-" + incident + "-a" + str(attempt)
        query = urlencode({"state": "all", "head": owner + ":" + branch,
                           "per_page": 100})
        pulls = api.request("GET", "/pulls?" + query)
        if not isinstance(pulls, list) or len(pulls) >= 100:
            raise ValueError("Unexpected or incomplete recovery PR history")
        for pull in pulls:
            # The API head filter is authoritative; reject a contradictory row.
            if pull.get("head", {}).get("ref") != branch:
                raise ValueError("Recovery PR head does not match its attempt")
            records.append((attempt, parse_timestamp(pull.get("created_at"))))
    return records


def check_once(api, driver, now, dry_run=False):
    snapshot = api.snapshot()
    decision = driver.decide(snapshot[1], snapshot[2], now)
    print(json.dumps(decision.__dict__), flush=True)
    if decision.action != "trigger":
        return decision.action
    incident = driver.incident_identity(snapshot[1], snapshot[2])
    records = request_history(api, incident, driver.timestamp,
                              driver.MAX_RECOVERY_ATTEMPTS)
    kind, attempt = next_signal(records, now, driver.ACK_TIMEOUT_SECONDS,
                                driver.MAX_RECOVERY_ATTEMPTS)
    print(json.dumps({"incident": incident, "signal": kind,
                      "attempt": attempt, "dry_run": dry_run}), flush=True)
    if dry_run or kind == "wait":
        return "dry-run" if dry_run else "wait"
    # Re-read after PR-history retrieval; a recovery may already have taken over.
    fresh = api.snapshot()
    current = driver.decide(fresh[1], fresh[2], datetime.now(timezone.utc))
    if (current.action != "trigger"
            or driver.incident_identity(fresh[1], fresh[2]) != incident):
        print("State advanced; no signal emitted", flush=True)
        return "changed"
    if kind == "alert":
        driver.emit_infrastructure_failure(api, fresh, attempt)
        return "alert"
    result = driver.emit_recovery(api, fresh, current, attempt)
    if result == "changed":
        return "changed"
    if result != "done":
        raise ValueError("Unexpected recovery emitter result")
    print("Request emitted, NOT recovery acknowledgement", flush=True)
    return "requested"


def main():
    import supervisor
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    api = supervisor.GitHubAPI(os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"])
    check_once(api, supervisor, datetime.now(timezone.utc), args.dry_run)


if __name__ == "__main__":
    main()
