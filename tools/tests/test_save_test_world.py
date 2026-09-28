import importlib.util
from pathlib import Path
import tempfile
import time
import unittest

spec = importlib.util.spec_from_file_location("save_test_world", Path(__file__).parents[1] / "save_test_world.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeClient:
    def __init__(self, log, responses):
        self.log, self.responses, self.calls = log, iter(responses), 0
        self.state = {"inGame": True, "updatedAtMs": time.time() * 1000}

    def require_live(self):
        pass

    def call(self, command, timeout):
        assert command == "say [Save"
        self.calls += 1
        with self.log.open("a") as handle:
            for message in next(self.responses, []):
                handle.write(f"[08:00:00 INF] {message} <s:Server.World>\n")


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log = Path(self.temp.name) / "server.log"
        self.log.write_text("[07:00:00 INF] Writing world save snapshot done (0.04 seconds) <s:Server.World>\n")

    def test_waits_for_new_disk_publication(self):
        client = FakeClient(self.log, [["Saving world", "Saving world done (0.02 seconds)",
                                       "Writing world save snapshot done (0.04 seconds)"]])
        self.assertEqual(module.save_world(client, self.log)["status"], "published")

    def test_serialization_message_is_not_disk_completion(self):
        client = FakeClient(self.log, [["Saving world", "Saving world done (0.02 seconds)"]])
        with self.assertRaises(TimeoutError):
            module.save_world(client, self.log, 0.15)

    def test_old_log_cannot_pass(self):
        with self.assertRaises(TimeoutError):
            module.save_world(FakeClient(self.log, [[]]), self.log, 0.15)

    def test_inflight_snapshot_requires_another_save(self):
        client = FakeClient(self.log, [["Writing world save snapshot done (0.04 seconds)"],
                                      ["Saving world", "Writing world save snapshot done (0.04 seconds)"]])
        self.assertEqual(module.save_world(client, self.log)["requests"], 2)

    def test_failure_is_not_success(self):
        for failure in ("Saving world failed", "Writing world save snapshot failed", "A WorldSave handler failed"):
            with self.subTest(failure=failure), self.assertRaises(RuntimeError):
                module.save_world(FakeClient(self.log, [[failure]]), self.log)

    def test_stale_snapshot_sends_nothing(self):
        client = FakeClient(self.log, [])
        client.state["updatedAtMs"] -= 6000
        with self.assertRaises(RuntimeError):
            module.save_world(client, self.log)
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
