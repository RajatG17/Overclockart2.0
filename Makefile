infra-up:
	docker compose up -d

infra-down:
	docker compose down

infra-status:
	docker compose ps

infra-logs:
	docker compose logs -f

k8s-status:
	kubectl get nodes

m0-check:
	docker compose ps
	kubectl get nodes
	