"""No-network regression tests for durable one-shot recovery signalling."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse
from oneshot import next_signal, check_once, request_history

NOW = datetime(2026, 10, 18, 19, 30, tzinfo=timezone.utc)

class DurableAttemptTests(unittest.TestCase):
    def test_first_request(self):
        self.assertEqual(next_signal([], NOW), ("request", 1))

    def test_wait_before_timeout(self):
        self.assertEqual(next_signal([(1, NOW-timedelta(seconds=359))], NOW), ("wait", 1))

    def test_retry_at_timeout(self):
        self.assertEqual(next_signal([(1, NOW-timedelta(seconds=360))], NOW), ("request", 2))

    def test_independent_invocation_uses_durable_history(self):
        history = [(1, NOW-timedelta(minutes=30)), (2, NOW-timedelta(minutes=7))]
        self.assertEqual(next_signal(history, NOW), ("request", 3))
        self.assertEqual(next_signal(list(history), NOW), ("request", 3))

    def test_alert_after_third_unacknowledged_request(self):
        self.assertEqual(next_signal([(3, NOW-timedelta(minutes=7))], NOW), ("alert", 3))

    def test_duplicate_request_wait_is_conservative(self):
        self.assertEqual(next_signal([(1, NOW-timedelta(minutes=9)), (1, NOW)], NOW), ("wait", 1))

    def test_future_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            next_signal([(1, NOW+timedelta(minutes=3))], NOW)

    def test_invalid_attempt_rejected(self):
        with self.assertRaises(ValueError):
            next_signal([(True, NOW)], NOW)

class DriverTests(unittest.TestCase):
    def fixtures(self):
        api = Mock(repo="tpuzz/delta14-watchdog-trigger")
        api.snapshot.return_value = ("sha", {"run_id":"old"}, {"generation":29})
        api.request.return_value = []
        driver = Mock(MAX_RECOVERY_ATTEMPTS=3, ACK_TIMEOUT_SECONDS=360)
        driver.decide.return_value = SimpleNamespace(action="trigger", reason="stale", mode="resume_within_original_scope")
        driver.incident_identity.return_value = "incident"
        driver.timestamp.side_effect = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        return api, driver

    def test_no_signal_when_lease_or_status_forbids_it(self):
        api, driver = self.fixtures()
        driver.decide.return_value = SimpleNamespace(action="wait", reason="live lease", mode="")
        self.assertEqual(check_once(api, driver, NOW), "wait")
        api.request.assert_not_called()
        driver.emit_recovery.assert_not_called()

    def test_first_request_and_no_false_ack(self):
        api, driver = self.fixtures()
        self.assertEqual(check_once(api, driver, NOW), "requested")
        self.assertEqual(driver.emit_recovery.call_args.args[-1], 1)
        driver.emit_infrastructure_failure.assert_not_called()

    def test_no_write_on_dry_run(self):
        api, driver = self.fixtures()
        self.assertEqual(check_once(api, driver, NOW, dry_run=True), "dry-run")
        driver.emit_recovery.assert_not_called()
        driver.emit_infrastructure_failure.assert_not_called()

    def test_changed_owner_during_history_read(self):
        api, driver = self.fixtures()
        driver.incident_identity.side_effect = ["incident", "successor"]
        self.assertEqual(check_once(api, driver, NOW), "changed")
        driver.emit_recovery.assert_not_called()
        driver.emit_infrastructure_failure.assert_not_called()

    def test_closed_pr_still_counts(self):
        api, driver = self.fixtures()
        def history(method, endpoint):
            head = parse_qs(urlparse(endpoint).query)["head"][0]
            branch = head.split(":",1)[1]
            if branch.endswith("-a1"):
                return [{"head":{"ref":branch},"state":"closed","created_at":"2026-10-18T19:00:00Z"}]
            return []
        api.request.side_effect = history
        self.assertEqual(check_once(api, driver, NOW), "requested")
        self.assertEqual(driver.emit_recovery.call_args.args[-1], 2)

    def test_mismatched_pr_rejected(self):
        api, driver = self.fixtures()
        api.request.return_value = [{"head":{"ref":"wrong"}, "created_at":"2026-10-18T19:00:00Z"}]
        with self.assertRaises(ValueError):
            request_history(api, "incident", driver.timestamp)

if __name__ == "__main__":
    unittest.main()
