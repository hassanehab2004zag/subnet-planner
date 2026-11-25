# subnet-planner

A small VLSM subnet planner in Python. Give it a parent network and the number of hosts each subnet needs, and it lays out non-overlapping subnets, largest first.

Practice project on test data. Not company work.

## Usage
```
python3 subnet_planner.py 10.20.0.0/16 "HQ=500" "Branch-A=60" "Branch-B=28" "P2P-VPN=2"
```
Prints each subnet with its network, mask and usable host count. A `/31` is used for 2-host point-to-point links.

## Tests
```
python3 -m unittest discover -s tests
```
7 unit tests, passed on Python 3.10 in a local test environment. They check subnet sizes, no overlap, everything inside the parent network, and error cases (zero hosts, parent too small, host bits set).

## Limits
IPv4 only. Standard library only. Not tested against real network devices.
