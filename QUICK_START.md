# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Verify services are healthy
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

## 3. Run Tests

```bash
# Unit tests (fast, no services needed)
cd user-service && pytest tests/test_unit.py -v && cd ..

# Integration tests (requires services)
pytest tests/test_integration.py -v

# E2E tests (requires services)
pytest tests/test_e2e.py -v
```

## 4. Try the API

```bash
# Get all users
curl http://localhost:5001/api/users | jq

# Get all products
curl http://localhost:5002/api/products | jq

# Create an order
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 2, "quantity": 2}' | jq

# Get all orders
curl http://localhost:5003/api/orders | jq
```

## 5. Stop Services

```bash
docker-compose down
```

## Using Make Commands

```bash
make help          # Show all commands
make build         # Build images
make up            # Start services
make test-unit     # Run unit tests
make test-all      # Run all tests
make down          # Stop services
make logs          # View logs
```

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check out [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for presentation guide
- Explore the test files to understand different testing approaches
- Modify the services to experiment with testing

## Service Ports

- User Service: http://localhost:5001
- Product Service: http://localhost:5002
- Order Service: http://localhost:5003

## Common Issues

**Services won't start:**
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

**Tests failing:**
```bash
# Make sure services are running
docker-compose ps

# Wait a bit longer for services
sleep 10
```

**Port conflicts:**
- Edit `docker-compose.yml` to change port mappings
- Or stop other services using ports 5001-5003

---

That's it! You're ready to explore microservices testing. 🚀
