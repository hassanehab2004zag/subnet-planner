# subnet-planner

A small VLSM subnet planner in Python. Give it a parent network and the number of hosts each subnet needs, and it lays out non-overlapping subnets, largest first.

Practice project on test data. Not company work.

## Usage
```
python3 subnet_planner.py 10.20.0.0/16 "HQ=500" "Branch-A=60" "Branch-B=28" "P2P-VPN=2"
```
Prints each subnet with its network, mask, first and last host and usable host count, then how much of the parent network is allocated. `--format csv|markdown|json` writes the plan as a table for documentation. Bad input gives a one-line error and exit code 2. A `/31` is used for 2-host point-to-point links.

## Example output
```
HQ           10.20.0.0/23       255.255.254.0    10.20.0.1 - 10.20.1.254 usable=510 (asked 500)
Branch-A     10.20.2.0/26       255.255.255.192  10.20.2.1 - 10.20.2.62 usable=62 (asked 60)
Branch-B     10.20.2.64/27      255.255.255.224  10.20.2.65 - 10.20.2.94 usable=30 (asked 28)
P2P-VPN      10.20.2.96/31      255.255.255.254  10.20.2.96 - 10.20.2.97 usable=2 (asked 2)
allocated 610 of 65536 addresses (0.9%)
```
With `--format markdown`, for `192.168.10.0/24 LAN=100 Link=2`:

| name | requested | network | mask | first_host | last_host | broadcast | usable |
|---|---|---|---|---|---|---|---|
| LAN | 100 | 192.168.10.0/25 | 255.255.255.128 | 192.168.10.1 | 192.168.10.126 | 192.168.10.127 | 126 |
| Link | 2 | 192.168.10.128/31 | 255.255.255.254 | 192.168.10.128 | 192.168.10.129 | - | 2 |

## Tests
```
python3 -m unittest discover -s tests
```
13 unit tests, passed on Python 3.10 in a local test environment. They check subnet sizes, no overlap, everything inside the parent network, error cases (zero hosts, parent too small, host bits set), host ranges, /31 handling, output formats, utilization and clean CLI errors.

## Limits
IPv4 only. Standard library only. Not tested against real network devices.
