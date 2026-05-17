#!/usr/bin/env bash
set -euo pipefail

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'

printf "check-project: unittest discover OK\n"
