# Dev Container Quick Guide

The dev container provides a complete testing environment with all dependencies pre-installed and access to all microservices via Docker DNS.

## Quick Start

1. **Build and start all services:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Enter the dev container:**
   ```bash
   make dev-shell
   ```

3. **Run tests inside the dev container:**
   ```bash
   # Unit tests (fast, no service dependencies)
   make test-unit

   # Integration tests (tests service-to-service communication)
   pytest tests/test_integration.py -v

   # End-to-end tests (complete workflows)
   pytest tests/test_e2e.py -v
   ```

## What's Included in the Dev Container?

- **Python 3.11** - Latest stable Python
- **make** - Build automation
- **All dependencies** - Flask, pytest, requests, etc.
- **Development tools** - ipython, ipdb for debugging
- **Network access** - Can reach services via DNS:
  - `user-service:5000`
  - `product-service:5000`
  - `order-service:5000`

## Running Tests

### From Inside the Dev Container

```bash
# Enter the container
make dev-shell

# Run any test command
make test-unit
pytest tests/test_integration.py -v
pytest tests/test_e2e.py -v
pytest tests/test_integration.py::TestOrderServiceIntegration::test_order_service_calls_user_service_successfully -v
```

### From Outside the Dev Container

```bash
# Run tests without entering the container
make dev-test-unit          # Unit tests
make dev-test-integration   # Integration tests
make dev-test-e2e           # E2E tests
make dev-test-all           # All tests
```

## Accessing Services

Inside the dev container, you can access services using their container names:

```bash
# Check service health
curl http://user-service:5000/health
curl http://product-service:5000/health
curl http://order-service:5000/health

# Test API endpoints
curl http://user-service:5000/api/users
curl http://product-service:5000/api/products
curl -X POST http://order-service:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 1, "quantity": 2}'
```

## Benefits

✅ **No local dependencies** - Don't need to install Python, pip, or packages on your host machine

✅ **Consistent environment** - Everyone uses the same Python version and dependencies

✅ **Network isolation** - Services communicate via Docker DNS, same as in production

✅ **Easy debugging** - Use ipdb or ipython inside the container

✅ **Fast iteration** - Code changes are immediately reflected (volume mount)

## Common Workflows

### Running a Single Test

```bash
make dev-shell
pytest tests/test_integration.py::TestOrderServiceIntegration::test_order_service_calls_user_service_successfully -v
```

### Running Tests with Coverage

```bash
make dev-shell
cd user-service
pytest tests/test_unit.py --cov=app --cov-report=html
```

### Interactive Debugging

```bash
make dev-shell

# Add ipdb breakpoint in your code:
# import ipdb; ipdb.set_trace()

# Run the test
pytest tests/test_integration.py -v -s
```

### Checking Service Logs

```bash
# From host machine
docker-compose logs -f user-service
docker-compose logs -f product-service
docker-compose logs -f order-service
```

## Troubleshooting

### Container not starting?
```bash
# Rebuild the dev container
docker-compose build dev-container
docker-compose up -d dev-container
```

### Services not reachable?
```bash
# Check if services are running
docker-compose ps

# Check service health
docker-compose exec dev-container curl http://user-service:5000/health
```

### Permission issues?
The dev container runs as root by default. If you encounter permission issues with created files, you can change ownership:
```bash
# From host
sudo chown -R $USER:$USER .
```

## Stopping Everything

```bash
# Stop all services including dev container
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
