#!/bin/bash

# Ensure python requirements are installed silently
pip install -r tests/requirements.txt > /dev/null 2>&1

# Run the beautiful rich demo
python scripts/live_demo.py
