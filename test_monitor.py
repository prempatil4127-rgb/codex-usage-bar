import json
import tempfile
import unittest
from pathlib import Path
from monitor import latest_usage, quota_display, anchor, latest_session
from windows_host import is_codex_path


class UsageTests(unittest.TestCase):
    def test_stationary_meter_does_not_reposition_repeatedly(self):
        from unittest.mock import patch
        import windows_host as host
        with patch.object(host, 'set_pos', return_value=True) as place:
            for _ in range(100):
                host.place(987654, 100, 200, 362, 44)
            self.assertEqual(place.call_count, 1)
            host.place(987654, 101, 200, 362, 44)
            self.assertEqual(place.call_count, 2)
            with patch.object(host, 'show') as hide:
                host.hide(987654)
                host.hide(987654)
                self.assertEqual(hide.call_count, 1)
            host.place(987654, 101, 200, 362, 44)
            self.assertEqual(place.call_count, 3)
            host._placements.pop(987654)

    def test_failed_position_is_retried(self):
        from unittest.mock import patch
        import windows_host as host
        with patch.object(host, 'set_pos', side_effect=[False, True]) as place:
            host.place(987655, 100, 200, 362, 44)
            host.place(987655, 100, 200, 362, 44)
            self.assertEqual(place.call_count, 2)
            host._placements.pop(987655)

    def test_anchor_stays_in_host_on_negative_monitor(self):
        self.assertEqual(anchor((-1920, 0, 0, 1080), 362, 44), (-386, 1024))
        self.assertEqual(anchor((0, 0, 800, 600), 362, 44, 9000, -9000), (438, 0))

    def test_host_is_desktop_app_not_cli_or_other_apps(self):
        self.assertTrue(is_codex_path(r'C:\Program Files\WindowsApps\OpenAI.Codex_26.1021_x64\app\ChatGPT.exe'))
        self.assertFalse(is_codex_path(r'C:\Users\me\bin\codex.exe'))
        self.assertFalse(is_codex_path(r'C:\Program Files\Chrome\chrome.exe'))

    def test_latest_chat_and_no_sessions(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(latest_session(root))
            day = root / '2026' / '10' / '27'
            day.mkdir(parents=True)
            old, new = day / 'old.jsonl', day / 'new.jsonl'
            old.touch()
            new.touch()
            os.utime(old, (10, 10))
            os.utime(new, (20, 20))
            self.assertEqual(latest_session(root), new)

    def test_partial_write_keeps_last_complete_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps({'timestamp': 'now', 'payload': {
                'type': 'token_count', 'info': {'total': 7},
                'rate_limits': {'primary': {'used_percent': 29}}
            }}) + '\n{"type":"token_count",broken\n')
            stamp, info, limits = latest_usage(path)
            self.assertEqual((stamp, info), ('now', {'total': 7}))
            self.assertEqual(limits['primary']['used_percent'], 29)

    def test_quota_windows_and_reset(self):
        limits = {'primary': {'used_percent': 29, 'window_minutes': 300, 'resets_at': 100},
                  'secondary': {'used_percent': 15, 'window_minutes': 10080}}
        self.assertEqual(quota_display(limits, 'primary', 99), ('5-hour: 29% used · 71% remaining', 29))
        self.assertEqual(quota_display(limits, 'secondary', 99), ('Weekly: 15% used · 85% remaining', 15))
        self.assertIn('awaiting', quota_display(limits, 'primary', 100)[0])
        self.assertEqual(quota_display(None, 'primary', 99), ('Quota unavailable', 0))


if __name__ == '__main__':
    unittest.main()
