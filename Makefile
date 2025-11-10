.PHONY: help build up down test test-unit test-integration test-e2e test-all logs clean dev-shell dev-test-unit dev-test-integration dev-test-e2e dev-test-all

help:
	@echo "Microservices Testing Demo - Available Commands:"
	@echo ""
	@echo "  make build              - Build all Docker images (including dev container)"
	@echo "  make up                 - Start all services (including dev container)"
	@echo "  make down               - Stop all services"
	@echo "  make test-unit          - Run unit tests (fast, no services needed)"
	@echo "  make test-integration   - Run integration tests (requires services)"
	@echo "  make test-e2e           - Run end-to-end tests (requires services)"
	@echo "  make test-all           - Run all tests"
	@echo "  make logs               - View logs from all services"
	@echo "  make clean              - Stop services and remove volumes"
	@echo ""
	@echo "Dev Container Commands:"
	@echo "  make dev-shell          - Enter the dev container shell"
	@echo "  make dev-test-unit      - Run unit tests from dev container"
	@echo "  make dev-test-integration - Run integration tests from dev container"
	@echo "  make dev-test-e2e       - Run end-to-end tests from dev container"
	@echo "  make dev-test-all       - Run all tests from dev container"
	@echo ""

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Services are ready!"
	@echo ""
	@echo "Service URLs:"
	@echo "  User Service:    http://localhost:5001"
	@echo "  Product Service: http://localhost:5002"
	@echo "  Order Service:   http://localhost:5003"

down:
	@echo "Stopping all services..."
	docker-compose down

test-unit:
	@echo "Running unit tests..."
	@echo ""
	@echo "=== User Service Unit Tests ==="
	cd user-service && python -m pytest tests/test_unit.py -v
	@echo ""
	@echo "=== Product Service Unit Tests ==="
	cd product-service && python -m pytest tests/test_unit.py -v
	@echo ""
	@echo "=== Order Service Unit Tests ==="
	cd order-service && python -m pytest tests/test_unit.py -v

test-integration:
	@echo "Running integration tests (requires services to be running)..."
	@echo "Make sure to run 'make up' first!"
	python -m pytest tests/test_integration.py -v

test-e2e:
	@echo "Running end-to-end tests (requires services to be running)..."
	@echo "Make sure to run 'make up' first!"
	python -m pytest tests/test_e2e.py -v

test-all: test-unit
	@echo ""
	@echo "Starting services for integration and E2E tests..."
	$(MAKE) up
	@sleep 5
	@echo ""
	@echo "Running integration tests..."
	$(MAKE) test-integration
	@echo ""
	@echo "Running end-to-end tests..."
	$(MAKE) test-e2e
	@echo ""
	@echo "Stopping services..."
	$(MAKE) down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	@echo "Cleaned up services and volumes"

# Dev Container Commands
dev-shell:
	@echo "Entering dev container shell..."
	@echo "You can now run tests with 'make test-unit', 'make test-integration', etc."
	@echo "Services are available at:"
	@echo "  - user-service:5000"
	@echo "  - product-service:5000"
	@echo "  - order-service:5000"
	@echo ""
	docker-compose exec dev-container /bin/bash

dev-test-unit:
	@echo "Running unit tests from dev container..."
	docker-compose exec dev-container make test-unit

dev-test-integration:
	@echo "Running integration tests from dev container..."
	docker-compose exec dev-container python -m pytest tests/test_integration.py -v

dev-test-e2e:
	@echo "Running end-to-end tests from dev container..."
	docker-compose exec dev-container python -m pytest tests/test_e2e.py -v

dev-test-all:
	@echo "Running all tests from dev container..."
	@echo ""
	@echo "=== Unit Tests ==="
	docker-compose exec dev-container make test-unit
	@echo ""
	@echo "=== Integration Tests ==="
	docker-compose exec dev-container python -m pytest tests/test_integration.py -v
	@echo ""
	@echo "=== End-to-End Tests ==="
	docker-compose exec dev-container python -m pytest tests/test_e2e.py -v
	@echo ""
	@echo "All tests completed!"
