#!/usr/bin/env bash

set -e
set -x

export PYTHONPATH=.
pytest --cov-report=html
