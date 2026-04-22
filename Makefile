.PHONY: cluster-up deploy test cluster-down

cluster-up:
	kind create cluster --name overclockkart

deploy:
	kubectl apply -f kubernetes/infrastructure/
	kubectl apply -f kubernetes/apisix/
	kubectl apply -f kubernetes/services/deployments.yaml

test:
	pip install -r tests/requirements.txt
	pytest tests/e2e/test_checkout_flow.py -v -s

cluster-down:
	kind delete cluster --name overclockkart
