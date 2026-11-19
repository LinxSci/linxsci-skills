#!/usr/bin/env python3
"""Validate candidate or final packages, checksums, identities and source snapshots."""
from skill_release import check_main, guarded

if __name__ == '__main__':
    guarded(check_main)
