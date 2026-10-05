import importlib.util
import signal
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

spec = importlib.util.spec_from_file_location(
    "hosted_supervisor", Path(__file__).parents[2] / "scripts" / "start-hosted.py"
)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


class HostedSupervisorTests(SimpleTestCase):
    def test_child_exit_stops_remaining_process_and_reports_failure(self):
        web, worker = Mock(), Mock()
        web.poll.return_value = 1
        worker.poll.return_value = None
        with patch.object(supervisor.subprocess, "Popen", side_effect=[web, worker]):
            self.assertEqual(supervisor.supervise([["web"], ["worker"]], "."), 1)
        worker.terminate.assert_called_once()
        worker.wait.assert_called_once_with(timeout=20)

    def test_partial_start_failure_cleans_up_started_child(self):
        web = Mock()
        web.poll.return_value = None
        with patch.object(
            supervisor.subprocess, "Popen", side_effect=[web, OSError("spawn failed")]
        ):
            with self.assertRaises(OSError):
                supervisor.supervise([["web"], ["worker"]], ".")
        web.terminate.assert_called_once()
        web.wait.assert_called_once_with(timeout=20)

    def test_shutdown_during_start_does_not_spawn_another_child(self):
        web = Mock()
        web.poll.return_value = None
        previous = signal.getsignal(signal.SIGTERM)

        def spawn(*args, **kwargs):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            return web

        with patch.object(supervisor.subprocess, "Popen", side_effect=spawn) as popen:
            self.assertEqual(supervisor.supervise([["web"], ["worker"]], "."), 0)
        self.assertEqual(popen.call_count, 1)
        web.terminate.assert_called_once()
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)

    def test_child_ignoring_termination_is_killed(self):
        child = Mock()
        child.poll.return_value = 1
        child.wait.side_effect = [subprocess.TimeoutExpired("web", 20), 1]
        with patch.object(supervisor.subprocess, "Popen", return_value=child):
            self.assertEqual(supervisor.supervise([["web"]], "."), 1)
        child.kill.assert_called_once()
