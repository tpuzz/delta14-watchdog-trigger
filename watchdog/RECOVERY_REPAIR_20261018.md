# Delta14 recovery repair - 2026-10-18

Scope: infrastructure repair for `delta14-mixed-tate-20261012T210157Z` only. Do not touch the Gabriel campaign or publish private mathematics.

## Current user directive and narrow interpretation

After the status report about generation 29's offline environment, the user explicitly instructed: "figure out what didn't work and how to fix it, then do it".

This authorizes repairing the recovery mechanism and recovering the interrupted `exact-class-finish-3h-20261018-v1` authorization, only within its remaining original scope and time. It does not authorize a new campaign, new three-hour window, fourth hour, clock reset, repeated completed gates, or work after the original reserve.

Immutable clocks:
- authorization_start_utc: 2026-10-18T18:03:52Z
- delivery_start_utc: 2026-10-18T20:53:52Z
- hard_deadline_utc: 2026-10-18T21:03:52Z

For this exact authorization, the old generation-29 fields `phase=finalize-only-runtime-boundary` and `further_mathematics_authorized=false` describe the now-ended broken execution. Under the user's subsequent repair instruction they are not a new user cancellation. A genuinely fresh, healthy recovery may resume the exact unfinished assignment before the unchanged reserve, after verifying private source bytes, current ownership and the actual capabilities required by the assignment. Do not rewrite history or claim that recovery has occurred merely because this file exists.

The private confirmed statement, scope, completed claims, version bindings, source qualifications, wave counts and replacement limits remain authoritative. At/after the reserve, administrative finalization and delivery only. Any later explicit user stop overrides this repair. No automatic successor authorization is granted.

## Confirmed faults

1. The execution heartbeat reports `409 Conflict, environment_offline: Environment is not connected`; the underlying service-side cause is not established. Stopping that execution was correct.
2. The deployed quota-saver GitHub workflow uses `supervisor.py --once` and a twice-daily schedule, not continuous minute polling. An initial successful check is not ongoing supervision.
3. The existing supervisor's acknowledgement/retry state is only held in memory, so --once discards it. Subsequent one-shot runs can keep finding attempt 1 without advancing retries.
4. Runtime interruption, authorization closure and verified terminal delivery need separate states. Missing/partial reports remain unverified.

## Required recovery and monitoring behavior

Use the existing Delta14 Recovery and Results task and Mixed-Tate Hourly Watchdog; do not create duplicates. Verify private source bytes and the actual next assignment. An unexpired competing lease forbids takeover. Read current owner and heartbeat immediately before a conditional claim. Claim a unique run ID and next generation only for a real recovery. Publish/read back matching private state and heartbeat before claiming success.

If a GitHub ownership write is rejected by automatic external-write review, do not retry/rephrase it. Apply the private-checkpoint fallback already explicitly authorized in the original task only after independently excluding a live execution; report shared coordination as UNARMED. A genuine SHA conflict or competing lease is not that fallback.

On an ordinary recoverable runtime failure, stop the current execution and preserve exact durable outputs. Do not turn it into a user cancellation. Record recovery eligibility under the original clocks. When connector control survives, conditionally release only the execution's own lease after it has stopped substantive work and published the interruption, then emit one recovery signal. If control is lost entirely, the hourly backup remains the silent-failure detector.

Respect the deployed quota-saving mode. Do not claim minute-level recovery or reintroduce a long-running private Actions job merely to repair monitoring. Persist attempt identity in GitHub PR metadata so one-shot checks can distinguish a new request, an unacknowledged request, and a successful recovery. A PR is only a wake-up request. Success requires a coherent fresh successor owner and heartbeat, followed by an actual persisted work result or a truthful capability-blocked report.

No change in this file removes safety, source-integrity, privacy, ownership, verification, or budget restrictions.
