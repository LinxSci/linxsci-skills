#!/usr/bin/env python3
"""Fetch fixed Git commits and build local candidate or final Skill assets."""
from skill_release import build_main, guarded

if __name__ == '__main__':
    guarded(build_main)
