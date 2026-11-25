import ipaddress
import os
import json
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from subnet_planner import plan, prefix_for_hosts, parse_requests, render, utilization


class PrefixTests(unittest.TestCase):
    def test_known_sizes(self):
        self.assertEqual(prefix_for_hosts(2), 31)
        self.assertEqual(prefix_for_hosts(3), 29)
        self.assertEqual(prefix_for_hosts(6), 29)
        self.assertEqual(prefix_for_hosts(7), 28)
        self.assertEqual(prefix_for_hosts(60), 26)
        self.assertEqual(prefix_for_hosts(62), 26)
        self.assertEqual(prefix_for_hosts(63), 25)
        self.assertEqual(prefix_for_hosts(500), 23)

    def test_rejects_zero(self):
        with self.assertRaises(ValueError):
            prefix_for_hosts(0)


class PlanTests(unittest.TestCase):
    REQ = [("HQ", 500), ("Branch-A", 60), ("Branch-B", 28), ("P2P", 2)]

    def test_no_overlap_and_inside_parent(self):
        rows = plan("10.20.0.0/16", self.REQ)
        nets = [ipaddress.ip_network(r["network"]) for r in rows]
        parent = ipaddress.ip_network("10.20.0.0/16")
        for n in nets:
            self.assertTrue(n.subnet_of(parent))
        for i, a in enumerate(nets):
            for b in nets[i + 1:]:
                self.assertFalse(a.overlaps(b))

    def test_each_fits_request(self):
        for r in plan("10.20.0.0/16", self.REQ):
            self.assertGreaterEqual(r["usable"], r["requested"])

    def test_exact_expected_layout(self):
        got = {r["name"]: r["network"] for r in plan("10.20.0.0/16", self.REQ)}
        self.assertEqual(got, {"HQ": "10.20.0.0/23", "Branch-A": "10.20.2.0/26",
                               "Branch-B": "10.20.2.64/27", "P2P": "10.20.2.96/31"})

    def test_too_small_parent(self):
        with self.assertRaises(ValueError):
            plan("192.168.1.0/28", [("A", 30)])

    def test_host_bits_set_rejected(self):
        with self.assertRaises(ValueError):
            plan("10.0.0.1/24", [("A", 10)])


SCRIPT = os.path.join(os.path.dirname(__file__), "..", "subnet_planner.py")


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.rows = plan("192.168.10.0/24", [("LAN", 100), ("Mgmt", 10), ("Link", 2)])

    def test_host_range_and_broadcast(self):
        lan = next(r for r in self.rows if r["name"] == "LAN")
        self.assertEqual((lan["network"], lan["first_host"], lan["last_host"], lan["broadcast"]),
                         ("192.168.10.0/25", "192.168.10.1", "192.168.10.126", "192.168.10.127"))

    def test_slash31_has_no_broadcast(self):
        link = next(r for r in self.rows if r["name"] == "Link")
        self.assertEqual(link["usable"], 2)
        self.assertEqual(link["broadcast"], "-")
        self.assertEqual(link["first_host"], link["network"].split("/")[0])

    def test_formats(self):
        self.assertEqual(len(json.loads(render(self.rows, "json"))), 3)
        self.assertEqual(len(render(self.rows, "csv").splitlines()), 4)
        self.assertTrue(render(self.rows, "markdown").startswith("| name |"))

    def test_utilization(self):
        self.assertEqual(utilization("192.168.10.0/24", self.rows), (128 + 16 + 2, 256))

    def test_parse_requests_rejects_bad_input(self):
        for bad in ["LAN", "LAN=abc", "=5"]:
            with self.assertRaises(ValueError):
                parse_requests([bad])

    def test_cli_error_is_clean_not_a_traceback(self):
        p = subprocess.run([sys.executable, SCRIPT, "10.0.0.0/30", "Big=500"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("too small", p.stderr)
        self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
