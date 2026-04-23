.PHONY: cluster-up deploy test cluster-down

cluster-up:
	kind create cluster --name overclockkart --config kind-config.yaml

deploy:
	docker build -t overclockkart/auth-service:latest services/auth
	docker build -t overclockkart/catalog-service:latest services/catalog
	docker build -t overclockkart/order-service:latest services/order
	docker build -t overclockkart/payment-service:latest services/payment
	kind load docker-image overclockkart/auth-service:latest --name overclockkart
	kind load docker-image overclockkart/catalog-service:latest --name overclockkart
	kind load docker-image overclockkart/order-service:latest --name overclockkart
	kind load docker-image overclockkart/payment-service:latest --name overclockkart
	kubectl apply -f kubernetes/infrastructure/
	kubectl apply -f kubernetes/apisix/
	kubectl apply -f kubernetes/services/deployments.yaml
	kubectl wait --for=condition=available --timeout=300s deployment/apisix deployment/auth-service deployment/catalog-service deployment/order-service deployment/payment-service

test:
	pip install -r tests/requirements.txt
	pytest tests/e2e/test_checkout_flow.py -v -s

cluster-down:
	kind delete cluster --name overclockkart
