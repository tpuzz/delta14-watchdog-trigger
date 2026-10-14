import copy
from datetime import datetime, timedelta, timezone
import unittest
from supervisor import CAMPAIGN, decide, emit_recovery, incident_identity, recovery_acknowledged

NOW = datetime(2026, 10, 13, 20, 40, tzinfo=timezone.utc)
def stamp(minutes):
    return (NOW + timedelta(minutes=minutes)).isoformat()

class WatchdogRegressionTests(unittest.TestCase):
    def setUp(self):
        self.h = dict(campaign_id=CAMPAIGN, run_id="run-A", status="running",
                      lease_generation=1, watchdog_recovery_armed=True, last_heartbeat_utc=stamp(-25),
                      hard_deadline_utc=stamp(60), delivery_start_utc=stamp(50))
        self.o = dict(campaign_id=CAMPAIGN, owner_run_id="run-A", generation=1,
                      status="active", lease_expires_utc=stamp(-5))
    def check(self, action, mode=""):
        result = decide(self.h, self.o, NOW)
        self.assertEqual((result.action, result.mode), (action, mode), result)
    def test_stale_running(self):
        self.check("trigger", "resume_within_original_scope")
    def test_unarmed_running_waits(self):
        self.h["watchdog_recovery_armed"]=False; self.check("wait")
    def test_fresh_running(self):
        self.h["last_heartbeat_utc"] = stamp(-4); self.check("wait")
    def test_explicit_interruption_does_not_wait_twenty_minutes(self):
        self.h.update(status="interrupted", watchdog_recovery_armed=False, last_heartbeat_utc=stamp(-1), terminal_delivery_complete=False)
        self.check("trigger", "resume_within_original_scope")
    def test_blocked_incomplete_delivery(self):
        self.h.update(status="blocked", last_heartbeat_utc=stamp(-1), terminal_delivery_complete=False)
        self.check("trigger", "resume_within_original_scope")
    def test_interrupted_waits_for_lease(self):
        self.h["status"]="interrupted"; self.o["lease_expires_utc"]=stamp(5); self.check("wait")
    def test_blocked_waits_for_lease(self):
        self.h["status"]="blocked"; self.o["lease_expires_utc"]=stamp(5); self.check("wait")
    def test_expired_deadline_only_finalization(self):
        self.h.update(hard_deadline_utc=stamp(-10), delivery_start_utc=stamp(-20))
        self.check("trigger", "finalize_only")
    def test_delivery_reserve_only_finalization(self):
        self.h.update(hard_deadline_utc=stamp(5), delivery_start_utc=stamp(-5))
        self.check("trigger", "finalize_only")
    def test_recorded_final_only_instruction(self):
        self.h.update(status="interrupted", recovery_directive="Do not resume substantive mathematics.")
        self.check("trigger", "finalize_only")
    def test_completed_but_undelivered(self):
        self.h.update(status="completed", terminal_delivery_complete=False)
        self.check("trigger", "finalize_only")
    def test_completed_verified_delivery_stops(self):
        self.h.update(status="completed", terminal_delivery_complete=True, dropbox_final_status_verified=True)
        self.check("stop")
    def test_interrupt_with_verified_delivery_stops(self):
        self.h.update(status="interrupted", terminal_delivery_complete=True, dropbox_final_status_verified=True)
        self.check("stop")
    def test_only_one_terminal_flag_is_insufficient(self):
        self.h.update(status="completed", terminal_delivery_complete=True)
        self.check("trigger", "finalize_only")
    def test_intentional_legacy_pause_stops(self):
        self.h["status"]="paused"; self.check("stop")
    def test_pause_incomplete_delivery_is_final_only(self):
        self.h.update(status="paused", terminal_delivery_complete=False); self.check("trigger", "finalize_only")
    def test_cancel_stops(self):
        self.h["status"]="cancelled"; self.check("stop")
    def test_owner_mismatch_waits(self):
        self.o["owner_run_id"]="run-B"; self.check("wait")
    def test_generation_mismatch_waits(self):
        self.o["generation"]=2; self.check("wait")
    def test_missing_owner_waits(self):
        self.o={}; self.check("wait")
    def test_invalid_lease_waits(self):
        self.o["lease_expires_utc"]="garbage"; self.check("wait")
    def test_missing_deadline_waits(self):
        del self.h["hard_deadline_utc"]; self.check("wait")
    def test_future_heartbeat_waits(self):
        self.h["last_heartbeat_utc"]=stamp(5); self.check("wait")
    def test_inactive_stops(self):
        self.h["status"]="inactive"; self.check("stop")
    def test_next_generation_new_incident(self):
        old=incident_identity(self.h,self.o); self.o["generation"]+=1
        self.assertNotEqual(old, incident_identity(self.h,self.o))
    def test_duplicate_signal_does_not_write(self):
        class FakeAPI:
            repo="tpuzz/delta14-watchdog-trigger"
            def request(self, method, endpoint, *args, **kwargs):
                assert method=="GET" and endpoint.startswith("/pulls?")
                return [{"html_url":"already-exists"}]
        self.assertEqual(emit_recovery(FakeAPI(),("sha",self.h,self.o),decide(self.h,self.o,NOW)),"done")

    def test_recovery_ack_requires_new_live_generation(self):
        old_h = copy.deepcopy(self.h)
        old_h["authorization_id"] = "auth-A"
        old_o = copy.deepcopy(self.o)
        new_h = copy.deepcopy(old_h)
        new_o = copy.deepcopy(old_o)
        self.assertFalse(recovery_acknowledged(old_h, old_o, new_h, new_o, NOW))
        new_o.update(owner_run_id="run-B", generation=2, status="active", lease_expires_utc=stamp(10))
        new_h.update(run_id="run-B", lease_generation=2, status="running",
                     authorization_id="auth-A", last_heartbeat_utc=stamp(0))
        self.assertTrue(recovery_acknowledged(old_h, old_o, new_h, new_o, NOW))
        new_h["authorization_id"] = "auth-B"
        self.assertFalse(recovery_acknowledged(old_h, old_o, new_h, new_o, NOW))

    def test_original_incident_replay(self):
        self.h.update(status="interrupted", last_heartbeat_utc="2026-10-13T20:09:45.763Z",
                      hard_deadline_utc="2026-10-13T21:02:18Z", delivery_start_utc="2026-10-13T20:52:18Z",
                      terminal_delivery_complete=False, dropbox_final_status_verified=False,
                      recovery_directive="Do not resume substantive mathematics. Reconciliation and delivery only.")
        self.o["lease_expires_utc"]="2026-10-13T20:21:39.603Z"
        before=datetime(2026,10,13,20,21,39,tzinfo=timezone.utc)
        after=datetime(2026,10,13,20,21,40,tzinfo=timezone.utc)
        self.assertEqual(decide(self.h,self.o,before).action,"wait")
        self.assertEqual(decide(self.h,self.o,after).mode,"finalize_only")
        self.assertEqual(decide(self.h,self.o,after).action,"trigger")

if __name__=="__main__":
    unittest.main()
