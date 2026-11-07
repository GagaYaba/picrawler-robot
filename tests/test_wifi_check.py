import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "wifi"))
import wifi_check as w  # noqa: E402
import wifi_tutorial as t  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_netsh_ssid_ignores_bssid(self):
        text = "    Name : Wi-Fi\n    SSID                   : Freebox_ab\n    BSSID                  : aa:bb:cc"
        self.assertEqual(w.parse_netsh(text), "Freebox_ab")

    def test_netsh_no_ssid(self):
        self.assertIsNone(w.parse_netsh("    State : disconnected"))

    def test_nmcli_escaped_colon(self):
        rows = w.parse_nmcli_terse("Livebox\\:5G:802-11-wireless:wlan0\nlo:loopback:lo")
        self.assertEqual(rows[0], ["Livebox:5G", "802-11-wireless", "wlan0"])
        self.assertEqual(rows[1][1], "loopback")

    def test_remote_list_uses_ssid_and_dedupes(self):
        text = "ACTIVE:Bbox-10A57558\nKNOWN:Bbox-10A57558\nKNOWN:Gaga\nKNOWN:Gaga\nKNOWN:\nKNOWN:Box:5G"
        active, known = w.parse_remote_list(text)
        self.assertEqual(active, "Bbox-10A57558")
        self.assertEqual(known, ["Bbox-10A57558", "Gaga", "Box:5G"])

    def test_remote_list_empty(self):
        self.assertEqual(w.parse_remote_list(""), (None, []))

    def test_verdict(self):
        base = {"error": None, "pc": "A", "known": ["A", "B"]}
        self.assertEqual(w.verdict(base), "ok")
        self.assertEqual(w.verdict({**base, "pc": "C"}), "different")
        self.assertEqual(w.verdict({**base, "pc": None}), "pc_unknown")
        self.assertEqual(w.verdict({**base, "error": "timeout"}), "unreachable")


class TutorialTests(unittest.TestCase):
    def test_every_step_has_title_and_text(self):
        for step in t.STEPS:
            self.assertTrue(step["title"] and step["text"])

    def test_commands_never_embed_a_secret(self):
        cmds = [c for step in t.STEPS for c in step["commands"]]
        self.assertTrue(cmds)
        psk_line = [c for c in cmds if "read -rs" in c]
        self.assertEqual(len(psk_line), 1)  # password typed without echo
        for c in cmds:
            self.assertNotRegex(c, r"wifi-sec\.psk\s+[^\"$\s]")  # only the $PSK variable is allowed

    def test_text_output_lists_all_steps(self):
        text = t.as_text()
        for step in t.STEPS:
            self.assertIn(step["title"], text)


if __name__ == "__main__":
    unittest.main()
