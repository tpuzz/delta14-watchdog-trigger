# Delta14 watchdog ownership protocol

Campaign: `delta14-mixed-tate-20261012T210157Z`

Purpose: prevent two Work sessions from performing substantive campaign work concurrently.

## Lease parameters

- Heartbeat target cadence: approximately 5 minutes.
- Ownership lease duration: 12 minutes.
- Watchdog stale threshold: 20 minutes.
- A recovery trigger is permitted only when both:
  1. the heartbeat is at least 20 minutes old; and
  2. the current ownership lease has expired.

## Invariant

No session may perform substantive mathematics, launch research roles, or publish campaign-frontier mutations unless it holds the current active lease in `watchdog/owner.json`.

A session holds the lease exactly when all of the following are true:

- `owner_run_id` equals that session's exact `run_id`;
- `status` is `active`;
- `lease_expires_utc` is later than the current UTC time;
- the session has read back the written file and verified those fields.

## Atomic claim

Before substantive work:

1. Fetch `watchdog/owner.json` from `main`, including its current blob SHA.
2. If it contains an unexpired active lease owned by another run, STOP. Do not overwrite it.
3. If the lease is inactive or expired, prepare a replacement with:
   - the same campaign ID;
   - `owner_run_id` = this session's exact run ID;
   - `generation` = previous generation + 1;
   - `status` = `active`;
   - `last_renewed_utc` = now;
   - `lease_expires_utc` = now + 12 minutes.
4. Update the file using the exact blob SHA fetched in step 1.
5. If that conditional update fails because the file changed, another session may have raced for ownership. Re-fetch and STOP unless the refreshed file proves this same run owns the lease.
6. Read the file back and verify ownership before any substantive work.

The blob-SHA precondition is the cross-session compare-and-swap primitive. Never claim ownership by writing without the exact previously fetched SHA.

## Heartbeat / renewal

Approximately every 5 minutes while control is available:

1. Fetch `watchdog/owner.json` and verify this run still owns an unexpired active lease.
2. Renew the lease to now + 12 minutes using the exact fetched blob SHA.
3. Read it back and verify.
4. Only after successful lease renewal, update `watchdog/heartbeat.json` and the Dropbox `HEARTBEAT.json`.
5. If lease renewal fails or ownership has changed, STOP substantive work immediately and checkpoint only what can safely be attributed to this run.

## Recovery claim

A recovered session does not inherit the old run's ownership.

It must independently execute the Atomic claim procedure above. It may claim an expired lease, incrementing `generation`, but must never steal an unexpired lease.

After a successful claim it should:

1. update `watchdog/heartbeat.json` to its new run ID and status `running`;
2. verify that heartbeat;
3. update `watchdog/start.signal` with its run ID and current UTC time to launch a fresh watchdog instance;
4. verify the start signal;
5. only then declare automatic recovery armed.

## Clean release

Before a normal completion or pause:

1. persist the newest coherent Dropbox frontier;
2. write terminal heartbeat status;
3. fetch `watchdog/owner.json` and verify this run owns it;
4. conditionally update it, preserving owner_run_id and generation, with:
   - `status` = `inactive`;
   - `last_renewed_utc` = now;
   - `lease_expires_utc` = now.
5. read back the release.

If the run crashes, it cannot release; the lease expires naturally after 12 minutes. The watchdog still waits for the 20-minute heartbeat-stale threshold before opening a recovery PR.

## Deadline rule

Ownership does not grant or extend mathematical authorization. Every recovered run preserves the campaign's existing hard deadline. If that deadline has expired, no substantive research may resume even if ownership can be claimed.


## Terminal status contract

Every clean terminal state, including `completed`, `paused`, `expired`, or `blocked`, must write

`/ChatGPT-Research-State/delta14-mixed-tate/FINAL_STATUS.md`

before releasing ownership.

`FINAL_STATUS.md` must be concise and self-contained, and must include:

- campaign ID;
- terminal status: exactly one of `completed`, `paused`, `expired`, or `blocked`;
- terminal UTC timestamp;
- final mathematical conclusion, explicitly distinguishing proved / disproved / unresolved;
- promoted or verifier-backed results reached in this run;
- unresolved claims or gaps;
- last safe frontier;
- exact first unfinished action, if any;
- reason for stopping;
- current hard deadline and whether it expired;
- newest relevant recovery/resume artifact names;
- recommended next step.

A run must not describe itself as cleanly completed or release its ownership lease until the Dropbox `FINAL_STATUS.md` write has succeeded and been read back or otherwise verified.

If writing `FINAL_STATUS.md` fails, record that terminal delivery is incomplete, preserve ownership long enough to make one bounded retry if allowed by the infrastructure-failure rules, and otherwise stop with status `blocked` or `interrupted` as appropriate. Never fabricate terminal delivery.

Future recovery sessions should treat a verified `FINAL_STATUS.md` with status `completed` or `expired` as strong evidence that no further substantive continuation should begin unless the user explicitly authorizes new work.
