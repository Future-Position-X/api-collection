#!/usr/bin/env bash

set -e
set -x

mypy --verbose app
black app --check
isort --check-only app
flake8
