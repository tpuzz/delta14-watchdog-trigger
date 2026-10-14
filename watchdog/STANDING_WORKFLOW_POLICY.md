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
- `active_math_elapsed_seconds`: cumulative time during which the assigned mechanism screen is actually doing substantive mathematics.
- `math_segment_start_utc`: start of the current active mathematical segment, if any.

The mechanism gate is reached when `active_math_elapsed_seconds >= 1200` (20 minutes), subject always to the unchanged delivery reserve and hard deadline. Technical bootstrap, coordinator transport outage, lease-expiry waiting, automatic recovery bootstrap, persistence-only reconciliation, and other infrastructure downtime do NOT consume the 20-minute mechanism allowance. They DO consume the fixed three-hour total authorization.

Immediately before substantive mathematics, start a math segment. On checkpoint, interruption, deliberate gate decision, or switch to verification, close the segment and add its elapsed wall time to `active_math_elapsed_seconds`. Recovery continues the same accumulator; it never resets it. Persist the accumulator and segment provenance in state/heartbeat at the next safe write.

Special continuation7 correction: the verified 08:03:28Z initial heartbeat still represented pre-math bootstrap, and mathematics stopped approximately 08:08:00Z. Charge a conservative 300 seconds of active mechanism work before the crash (which is at least as much as the observed maximum from those durable bounds), leaving 900 seconds of the 1200-second mechanism allowance. The generation-5 finalize-only decision based on the obsolete 08:15:47Z launch-derived gate is superseded administratively. If the original hard deadline and delivery reserve are still live, a checked recovery may resume only the exact unfinished V/FRAME-DESCENT screen with `active_math_elapsed_seconds=300`; this is not a new authorization or an extension of total time.

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

Reuse the existing GitHub/Dropbox ownership, heartbeat, supervisor and recovery/results task. Do not create duplicates. The two standing recovery consumers are infrastructure: if one is found disabled while the campaign is active or recoverable, the other may re-enable that existing task and must report the incident.

- heartbeat target: about 5 minutes while control is available;
- cooperative ownership lease: 12 minutes;
- active supervisor polling: 60 seconds;
- silent-running recovery threshold: 20-minute stale heartbeat AND matching expired lease;
- explicit interrupted/blocked incomplete-delivery recovery: matching lease expiry, with no extra 20-minute wait.
- recovery request acknowledgement: opening a recovery PR is NOT recovery success; success requires a coherent successor owner generation plus matching fresh heartbeat under the same authorization/deadline.
- acknowledgement timeout: about 6 minutes; while the original authorization remains recoverable, retry the wake-up with a distinct attempt identifier, at most three attempts.
- after repeated unacknowledged wake-ups, emit a dedicated infrastructure-failure signal rather than silently stopping.
- the event-triggered recovery/results task and hourly backup are standing infrastructure. A disabled recovery consumer during an active/recoverable campaign is an infrastructure fault, not a reason to abandon recovery.

The cooperative lease is not a server-side fence on Dropbox writes. Recheck ownership before advancing a shared current-state pointer and after long operations.

Every complete new proof/audit/reconstruction/comparison report AND its actual input/output manifest must be externally persisted and byte-verified before the next verification role. Do not recreate lost reports from hashes or summaries.

At/after delivery reserve or hard deadline, recovery is finalize-only. Deliberate mathematical pause, explicit user stop/cancel and verified completion must not be restarted automatically.

On clean stop publish/read back the current immutable run-specific FINAL_STATUS, generation and compact resume capsule, send one terminal signal, and conditionally release ownership. The recovery/results task supplies completion reporting independently of the original conversation.

This policy changes workflow engineering only. It grants no new mathematical scope or total time and never permits bypassing safety, connector, ownership or verification requirements.
