#!/bin/bash
# Change les identifiants Comptexpert / redéclare le serveur auprès de Claude.
cd "$(dirname "$0")" && ./.venv/bin/python scripts/configure.py
