import ipaddress
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from subnet_planner import plan, prefix_for_hosts


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


if __name__ == "__main__":
    unittest.main()
