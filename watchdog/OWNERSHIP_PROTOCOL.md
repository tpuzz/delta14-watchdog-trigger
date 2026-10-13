# Delta14 watchdog ownership protocol

Campaign: `delta14-mixed-tate-20261012T210157Z`

Purpose: cooperative single-owner coordination for campaign work and publication. A lease is not a server-enforced fence on Dropbox writes or proof that a suspended process has terminated. Every participating session must obey the ownership checks, and recovery must independently verify the current frontier and interruption evidence.

## Lease parameters and recovery decisions

- Heartbeat target cadence: approximately 5 minutes.
- Ownership lease duration: 12 minutes.
- Supervisor polling interval while its GitHub Actions job is active: 60 seconds.
- For a `running` or `checkpointed` execution, request recovery only after a 20-minute stale heartbeat AND expiry of the matching ownership lease.
- For `interrupted` or `blocked` with unverified/incomplete terminal delivery, request recovery after expiry of the matching lease, WITHOUT an additional 20-minute wait. An interrupted run setting `watchdog_recovery_armed=false` does not erase this explicit failure signal.
- A terminal status with BOTH `terminal_delivery_complete=true` and `dropbox_final_status_verified=true` is left stopped.
- Cancellation, explicit user stop, inactivity and a deliberate legacy pause are not invitations to resume research.
- Missing clocks, missing ownership, mismatched run IDs or mismatched generations never authorize takeover.
- Recovery requests are deduplicated by campaign/run/generation. A new ownership generation has a distinct incident identity.

The implementation and regression tests are `watchdog/supervisor.py` and `watchdog/test_supervisor.py`.

## Invariant

No session may perform substantive mathematics, launch research roles, or publish campaign-frontier mutations unless it holds the current active lease in `watchdog/owner.json`.

A session holds the lease exactly when all of the following are true:

- `owner_run_id` equals that session's exact `run_id`;
- `status` is `active`;
- `lease_expires_utc` is later than the current UTC time;
- its recorded generation equals the current generation;
- the session has read back the written file and verified those fields.

Recheck ownership before publishing a shared checkpoint and after returning from a long operation. A session waking after lease expiry must not publish under its old generation. Preserve uncommitted work in a run-specific location instead of overwriting another owner's frontier.

## Atomic claim

Before substantive work or mutation of shared campaign state:

1. Fetch `watchdog/owner.json` from `main`, including its current blob SHA.
2. If it contains an unexpired active lease owned by another run, STOP. Do not overwrite it.
3. If the lease is inactive or expired and takeover is otherwise authorized, prepare a replacement with:
   - the same campaign ID;
   - `owner_run_id` = this session's exact run ID;
   - `generation` = previous generation + 1;
   - `status` = `active`;
   - `last_renewed_utc` = now;
   - `lease_expires_utc` = now + 12 minutes.
4. Update the file using the exact blob SHA fetched in step 1.
5. If that conditional update fails because the file changed, re-fetch and STOP unless the refreshed file proves this same run owns the lease.
6. Read the file back and verify ownership before proceeding.

The blob-SHA precondition protects this ownership-file update against conflicting versions. It does not make independent Dropbox writes atomic with the lease.

## Heartbeat / renewal

Approximately every 5 minutes while control is available:

1. Fetch `watchdog/owner.json` and verify this run still owns an unexpired active lease.
2. Renew the lease to now + 12 minutes using the exact fetched blob SHA.
3. Read it back and verify.
4. Only after successful lease renewal, update `watchdog/heartbeat.json` and the Dropbox `HEARTBEAT.json`, including `lease_generation`.
5. If lease renewal fails or ownership has changed, STOP substantive work and do not overwrite the shared frontier.

## Recovery claim

A recovered session does not inherit the old run's ownership. It must independently execute the Atomic claim procedure. It may claim an expired lease only after checking the incident and current state, and must never steal an unexpired lease.

After a successful claim:

1. Update `watchdog/heartbeat.json` to the new run ID, generation and status `running`, preserving the original authorization/deadline.
2. Verify that heartbeat and the corresponding Dropbox state.
3. Update `watchdog/start.signal` with the run ID and current UTC time to launch a fresh watchdog instance.
4. Verify the start signal and inspect the actual Actions run. File existence alone does not prove the supervisor is operating.
5. Record the exact infrastructure verification level. Do not infer successful end-to-end Work recovery merely from a heartbeat's `watchdog_recovery_armed` field.

Recovery PRs are requests for independent verification, not authority to skip lease checks, extend deadlines, reopen paused scope or trust missing audit artifacts. Re-read current state: a fresh owner or verified completed delivery supersedes an old PR.

## Deadline rule

Ownership does not grant or extend mathematical authorization. Every recovered run preserves the existing hard deadline and delivery reserve.

At or after the delivery-reserve start, or whenever the saved directive forbids further mathematics, the only permitted recovery mode is `finalize_only`: reconcile, persist and deliver existing results. Deadline expiry must not suppress a request to finish this administrative finalization, but it never authorizes new mathematics, repeated gates or a successor campaign. If the saved deadline is missing or invalid, do not invent one.

## Terminal status contract

Before a clean completion, pause, expiry stop or blocked stop, write and verify:

`/ChatGPT-Research-State/delta14-mixed-tate/FINAL_STATUS.md`

Include campaign ID; terminal status; terminal UTC timestamp; proved/disproved/unresolved conclusion; exact earned verification labels; residual gaps; last safe frontier; first unfinished action; stop reason; unchanged deadline; relevant artifact names; and recommended next step.

A hash or PASS attestation does not replace missing proof/audit bytes. Preserve any recorded verdict without inventing its report and disclose artifact-recovery limitations explicitly.

## Clean terminal publication and release

1. Persist the newest coherent Dropbox frontier, terminal capsule and `FINAL_STATUS.md`; verify their writes.
2. Publish a terminal GitHub heartbeat with the correct status and truthful `terminal_delivery_complete` and `dropbox_final_status_verified` booleans.
3. Write `watchdog/terminal.signal` ONCE for this run/status, containing run ID, generation, terminal status and UTC timestamp. Verify the write. Ordinary heartbeat updates must not touch this signal. The terminal notifier watches this dedicated signal, not heartbeat changes.
4. Fetch ownership, verify this run/generation still owns it, and conditionally release using the current SHA: preserve owner_run_id/generation; set `status=inactive`, `last_renewed_utc=now`, `lease_expires_utc=now`.
5. Read back the release. An external terminal notification is not proof of a mathematical result.

If terminal persistence fails, record `interrupted` or `blocked` with `terminal_delivery_complete=false` and `dropbox_final_status_verified=false`, save whatever exact evidence remains accessible, and follow the bounded infrastructure-stop rules. Do not fabricate delivery or silently convert the failure into a clean stop. Do not renew ownership indefinitely after stopping; expiry permits a separately checked finalization recovery.

The supervisor requests recovery but does not itself claim the lease or modify research results. It runs only when started by the configured Actions trigger; it is not an always-on service, and its bounded job can itself fail. Such failures must be reported rather than hidden or retried without limit.
