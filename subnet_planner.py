"""VLSM subnet planner: split a parent network into subnets sized by host count.

Usage:
    python3 subnet_planner.py 10.20.0.0/16 "HQ=500" "Branch-A=60" "Branch-B=28" "P2P-VPN=2"
"""
import ipaddress
import math
import sys


def prefix_for_hosts(hosts: int) -> int:
    """Smallest prefix length that fits `hosts` usable addresses (IPv4)."""
    if hosts < 1:
        raise ValueError("hosts must be at least 1")
    if hosts == 2:
        return 31  # point-to-point links, RFC 3021
    needed = hosts + 2  # network + broadcast
    return 32 - math.ceil(math.log2(needed))


def plan(parent: str, requests):
    """requests: list of (name, hosts). Returns a list of dicts, largest subnet first."""
    net = ipaddress.ip_network(parent, strict=True)
    if net.version != 4:
        raise ValueError("IPv4 only")
    sized = sorted(((n, h, prefix_for_hosts(h)) for n, h in requests), key=lambda x: x[2])
    cursor = int(net.network_address)
    end = int(net.broadcast_address)
    out = []
    for name, hosts, prefix in sized:
        size = 2 ** (32 - prefix)
        if cursor % size:
            cursor += size - cursor % size  # align to subnet boundary
        if cursor + size - 1 > end:
            raise ValueError(f"{parent} is too small for {name} ({hosts} hosts)")
        sub = ipaddress.ip_network((cursor, prefix))
        usable = size - 2 if prefix < 31 else size
        out.append({"name": name, "requested": hosts, "network": str(sub), "mask": str(sub.netmask), "usable": usable})
        cursor += size
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    reqs = []
    for item in argv[2:]:
        name, _, hosts = item.partition("=")
        reqs.append((name, int(hosts)))
    for row in plan(argv[1], reqs):
        print(f'{row["name"]:<12} {row["network"]:<18} {row["mask"]:<16} usable={row["usable"]} (asked {row["requested"]})')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
