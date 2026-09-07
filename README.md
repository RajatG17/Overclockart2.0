# Overclockart

"Event-driven commerce platform."

## Services

- Auth
- Catalog
- Order
- Payment

## Infrastructure

- PostgreSQL
- RabbitMQ
- Redis
- Kubernetes via k3d

## Local Infrastructure

```bash
docker compose up -d
docker compose ps
```

## Kubernetes

```bash
k3d cluster create commerce-local
kubectl get nodes

