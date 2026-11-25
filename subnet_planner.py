"""VLSM subnet planner: split a parent network into subnets sized by host count.

Usage:
    python3 subnet_planner.py 10.20.0.0/16 "HQ=500" "Branch-A=60" "Branch-B=28" "P2P-VPN=2"
"""
import argparse
import csv
import io
import ipaddress
import json
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
        first = sub.network_address + (1 if prefix < 31 else 0)
        last = sub.broadcast_address - (1 if prefix < 31 else 0)
        out.append({"name": name, "requested": hosts, "network": str(sub), "mask": str(sub.netmask),
                    "first_host": str(first), "last_host": str(last),
                    "broadcast": str(sub.broadcast_address) if prefix < 31 else "-", "usable": usable})
        cursor += size
    return out


FIELDS = ["name", "requested", "network", "mask", "first_host", "last_host", "broadcast", "usable"]


def parse_requests(items):
    reqs = []
    for item in items:
        name, sep, hosts = item.partition("=")
        if not sep or not name.strip() or not hosts.strip().isdigit():
            raise ValueError(f"bad request {item!r}, expected NAME=HOSTS")
        reqs.append((name.strip(), int(hosts)))
    return reqs


def render(rows, fmt):
    if fmt == "json":
        return json.dumps(rows, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue().rstrip("\n")
    if fmt == "markdown":
        lines = ["| " + " | ".join(FIELDS) + " |", "|" + "---|" * len(FIELDS)]
        lines += ["| " + " | ".join(str(r[f]) for f in FIELDS) + " |" for r in rows]
        return "\n".join(lines)
    return "\n".join(
        f'{r["name"]:<12} {r["network"]:<18} {r["mask"]:<16} {r["first_host"]} - {r["last_host"]}'
        f' usable={r["usable"]} (asked {r["requested"]})' for r in rows)


def utilization(parent, rows):
    total = ipaddress.ip_network(parent).num_addresses
    used = sum(ipaddress.ip_network(r["network"]).num_addresses for r in rows)
    return used, total


def main(argv):
    p = argparse.ArgumentParser(description="VLSM subnet planner. Requests look like NAME=HOSTS.")
    p.add_argument("parent")
    p.add_argument("requests", nargs="+")
    p.add_argument("--format", choices=["text", "csv", "markdown", "json"], default="text")
    try:
        args = p.parse_args(argv[1:])
    except SystemExit:
        return 2
    try:
        rows = plan(args.parent, parse_requests(args.requests))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(render(rows, args.format))
    if args.format == "text":
        used, total = utilization(args.parent, rows)
        print(f"allocated {used} of {total} addresses ({used / total:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
