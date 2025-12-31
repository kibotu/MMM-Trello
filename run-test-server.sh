#!/bin/bash
# Run script for MMM-Trello test server using uv
cd "$(dirname "$0")"
uv run test-server.py
