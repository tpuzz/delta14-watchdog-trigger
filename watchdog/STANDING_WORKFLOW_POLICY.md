# Standing workflow policy

Campaign: `delta14-mixed-tate-20261012T210157Z`

Standing user directive: always use the campaign's automatic recovery mechanism for every future explicitly authorized Work launch or continuation.

## Mandatory but lightweight launch bootstrap

Preparing or uploading a kit is NOT a launch. At an actual authorized launch, the hard total deadline starts from the launch/intake time and NEVER moves because of setup, recovery, or a crash.

Before substantive mathematics, do only the mandatory recovery bootstrap:

1. fetch/materialize the exact authorized launch kit and verify its expected SHA-256;
2. read only the minimal launch/read-order files needed to identify the authorization, frozen statement, current frontier and first assignment;
3. conditionally claim `watchdog/owner.json` using its freshly fetched blob SHA and read back the lease;
4. publish/read back ONE minimal immutable initial Dropbox state plus matching heartbeat;
5. update/read back `watchdog/start.signal`;
6. inspect the actual GitHub Actions supervisor job and verify that it really started (including its regression preflight when exposed).

Do NOT pre-read old proofs/audits, recursively scan the campaign, regenerate a large resume capsule, rebuild SHARE, or perform historical reconciliation before mathematics unless a concrete inconsistency makes that necessary. Lazy-load old evidence only when the mathematical assignment actually needs it.

Engineering target: normally complete this mandatory bootstrap in roughly 2-4 minutes. This is a soft operational target, not a correctness guarantee. If optional bookkeeping would push bootstrap beyond about 4 minutes, defer it. If a mandatory capability is unavailable or inconsistent, stop with the exact infrastructure blocker rather than running unmonitored.

The initial external state should be small: authorization identity, immutable clocks, source-kit/path/hash bindings, promoted-frontier pointer, exact first assignment, owner generation, and heartbeat/supervisor evidence. A full compact resume capsule may be generated at the first mathematical checkpoint instead of before math, provided the verified source kit and minimal state suffice to reconstruct the first assignment.

## Mathematical mechanism-gate clock

Separate the total authorization clock from the local feasibility gate.

- `authorization_start_utc`: actual launch/intake time.
- `hard_deadline_utc`: authorization start + the user-authorized total duration. Immutable.
- `delivery_start_utc`: unchanged reserve start before the hard deadline.
- `math_start_utc`: first instant AFTER the mandatory bootstrap when the coordinator actually begins the first substantive mathematical assignment.
- nominal `mechanism_gate_utc = math_start_utc + 20 minutes`, capped by `delivery_start_utc` if necessary.

The total budget includes bootstrap and recovery. Only the local 20-minute mechanism gate is measured from mathematical start.

Record `math_start_utc` immediately before the first substantive mathematical action and persist it in the next heartbeat/state update. Once recorded, recovery preserves it and NEVER resets the mechanism gate.

Special amendment for the interrupted continuation7 V-generic-descent launch: its initial durable state recorded `research_started=false` and no durable `math_start_utc`. If recovery confirms that no substantive mathematical checkpoint/return was persisted before the transport failure, the recovered run may set `math_start_utc` at its first recovered substantive mathematical action and receive the full nominal 20-minute mechanism gate from there, subject to the ORIGINAL hard deadline and delivery reserve. This does not create a new authorization or extend the three-hour total window.

## Lightweight recovery bootstrap

A recovery run is not a fresh launch and must not replay the full technical bootstrap.

After independent interruption checks and matching lease expiry:

1. read the live owner/heartbeat and the exact current immutable generation named by the heartbeat;
2. verify the unchanged authorization ID, hard deadline, delivery reserve, source-kit hash and exact first unfinished action;
3. claim the expired lease conditionally, incrementing generation, and read it back;
4. publish/read back a minimal recovery state + heartbeat;
5. update/read back `start.signal` and verify the actual supervisor job;
6. resume the exact unfinished assignment.

Do NOT re-download/re-hash already verified static predecessor artifacts, rebuild the whole capsule, reread historical audits, or redo completed gates unless current state shows a concrete integrity ambiguity. Recovery should normally consume only a small number of minutes. It keeps the same authorization clock, and if `math_start_utc` already exists it keeps the same mechanism gate.

## Monitoring and persistence

Reuse the existing GitHub/Dropbox ownership, heartbeat, supervisor and recovery/results task. Do not create duplicates or silently reactivate disabled tasks.

- heartbeat target: about 5 minutes while control is available;
- cooperative ownership lease: 12 minutes;
- active supervisor polling: 60 seconds;
- silent-running recovery threshold: 20-minute stale heartbeat AND matching expired lease;
- explicit interrupted/blocked incomplete-delivery recovery: matching lease expiry, with no extra 20-minute wait.

The cooperative lease is not a server-side fence on Dropbox writes. Recheck ownership before advancing a shared current-state pointer and after long operations.

Every complete new proof/audit/reconstruction/comparison report AND its actual input/output manifest must be externally persisted and byte-verified before the next verification role. Do not recreate lost reports from hashes or summaries.

At/after delivery reserve or hard deadline, recovery is finalize-only. Deliberate mathematical pause, explicit user stop/cancel and verified completion must not be restarted automatically.

On clean stop publish/read back the current immutable run-specific FINAL_STATUS, generation and compact resume capsule, send one terminal signal, and conditionally release ownership. The recovery/results task supplies completion reporting independently of the original conversation.

This policy changes workflow engineering only. It grants no new mathematical scope or total time and never permits bypassing safety, connector, ownership or verification requirements.
