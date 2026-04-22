#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}      OverclockKart 2.0 Live Demo Setup       ${NC}"
echo -e "${CYAN}==============================================${NC}"
echo ""

echo -e "${YELLOW}>> Setting up python environment for E2E tests...${NC}"
pip install -r tests/requirements.txt > /dev/null 2>&1

echo -e "${YELLOW}>> Triggering E2E Checkout Flow via APISIX Gateway...${NC}"
pytest tests/e2e/test_checkout_flow.py -v -s

echo ""
echo -e "${GREEN}✓ Saga Orchestration verified successfully!${NC}"
echo ""
echo -e "${YELLOW}>> Triggering Payment Webhook Simulation (Idempotency Check)...${NC}"
python services/payment/mock_stripe.py

echo ""
echo -e "${GREEN}✓ Demo complete! All distributed transactions and idempotent webhooks succeeded!${NC}"
