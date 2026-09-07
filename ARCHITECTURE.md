# Architecture

## Service boundaries

### Auth Service
Owns users and authentication data.

### Catalog Service
Owns products and inventory.

### Order Service
Owns orders and orchestrates order workflows.

### Payment Service
Owns payment integration and webhook processing.

## Data ownership

Each stateful domain service owns its database.

Services must not query another service's database directly.

## Local development

Application dependencies run through Docker Compose during early development.

Kubernetes deployment is introduced after the core application flow works.