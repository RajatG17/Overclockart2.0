# Test Suite Overview

This folder contains the unit test suite for the Overclockart 2.0 microservices architecture. The tests are organized by service to ensure isolation and clarity.

## Services Covered
- **Auth Service**: User registration, login, token verification, and security helpers.
- **Catalog Service**: Product management, inventory checks, and reservation logic.
- **Order Service**: Order creation, total calculation, and order history.
- **Payment Service**: Health check endpoint validation.

## Prerequisites
Before running the tests, ensure you have the following installed:
- Python 3.9+
- `pytest`
- `pytest-asyncio` (required for testing asynchronous routes)
- `httpx` (for FastAPI test client support)

You can install the necessary dependencies using the root `requirements.txt`:
```bash
pip install -r requirements.txt
```

## How to Run Tests

All tests should be executed from the **root directory** of the project (`Overclockart2.0`).

### 1. Run All Tests
To run every test in the entire project:
```bash
pytest
```

### 2. Run Tests for a Specific Service
If you only want to run tests for a particular service, use the following commands:

**Auth Service:**
```bash
pytest tests/auth/
```

**Catalog Service:**
```bash
pytest tests/catalog/
```

**Order Service:**
```bash
pytest tests/order/
```

**Payment Service:**
```bash
pytest tests/payment/
```

### 3. Run Tests with Verbose Output
To see more detailed information about each test case:
```bash
pytest -v
```

### 4. Run Specific Test Files
If you want to target a single file:
```bash
pytest tests/auth/test_auth_routes.py
```
