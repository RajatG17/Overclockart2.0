# Unit Test Plan

This document outlines the plan for implementing unit tests across all services in the project.

## Testing Strategy
- **Framework**: `pytest`
- **HTTP Client**: `httpx` (for FastAPI endpoint testing)
- **Database Mocking**: Use a dedicated test database or mock the repository/database layer to ensure isolation.
- **Structure**: Tests will be organized into service-specific folders within the `tests/` directory.

---

## 1. Auth Service
**Location**: `services/auth`
**Test Cases**:
- [ ] `POST /auth/register`:
    - Success with unique email.
    - Failure with already registered email (409 Conflict).
    - Validation errors for missing or malformed fields.
- [ ] `POST /auth/login`:
    - Success with correct credentials (returns token).
    - Failure with incorrect password (401 Unauthorized).
    - Failure with non-existent user (401 Unauthorized).
- [ ] `GET /auth/me`:
    - Success with valid JWT.
    - Failure with expired or invalid JWT.
- [ ] **Security Helpers**:
    - Password hashing and verification integrity.
    - Token generation and expiration logic.

## 2. Catalog Service
**Location**: `services/catalog`
**Test Cases**:
- [ ] `POST /catalog/products`:
    - Success: Create product and associated inventory.
    - Validation errors for negative prices or invalid quantities.
- [ ] `GET /catalog/products/{product_id}`:
    - Success: Return correct product details.
    - Failure: Return 404 for non-existent ID.
- [ ] `GET /catalog/products/{product_id}/inventory`:
    - Success: Return current inventory levels.
    - Failure: Return 404 for missing inventory records.
- [ ] `POST /catalog/inventory/{product_id}/reserve`:
    - Success: Decrease available quantity, increase reserved quantity.
    - Failure (409 Conflict): Insufficient available quantity.
    - Failure (404): Product ID does not exist.
- [ ] `POST /catalog/inventory/{product_id}/release`:
    - Success: Increase available quantity, decrease reserved quantity.
    - Failure (409 Conflict): Insufficient reserved quantity.

## 3. Order Service
**Location**: `services/order`
**Test Cases**:
- [ ] `POST /orders`:
    - Success: Create order and outbox event in a single transaction.
    - Verification of total calculation logic (`calculate_total`).
    - Integrity check for OutboxEvent payload structure.
- [ ] `GET /orders/{order_id}`:
    - Success: Retrieve complete order with items.
    - Failure: 404 for non-existent order.
- [ ] `GET /orders`:
    - Success: List all orders sorted by date.
- [ ] **Helpers**:
    - Unit test for `calculate_total` with various item combinations (empty, single, multiple).

## 4. Payment Service
**Location**: `services/payment`
**Test Cases**:
- [ ] `GET /health/live`: Ensure "ok" status is returned.
- [ ] `GET /health/ready`: Ensure "ready" status is returned.

---

## Next Steps
1. Set up a test environment (e.g., local SQLite or Dockerized Postgres).
2. Implement auth service tests first to establish common patterns.
3. Gradually move through catalog, order, and payment services.
