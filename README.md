# Microservices Testing Demonstration

A practical example of testing microservices architecture, demonstrating various testing methods including unit tests, integration tests, end-to-end tests, and mocking strategies.

## 🎯 Purpose

This project demonstrates how to test microservices based on the concepts from the "How are Microservices Tested?" presentation. It provides a working e-commerce system with three microservices that you can use for live testing demonstrations.

## 🏗️ Architecture

### System Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      ┌─────────────────┐
│  Order Service  │─────▶│  User Service   │
│   (Port 5003)   │      │   (Port 5001)   │
└────────┬────────┘      └─────────────────┘
         │
         │               ┌─────────────────┐
         └──────────────▶│ Product Service │
                         │   (Port 5002)   │
                         └─────────────────┘
```

### Services

1. **User Service** (Port 5001)
   - Manages user authentication and profiles
   - Validates user existence and status
   - Endpoints: `/api/users`, `/api/users/{id}/validate`

2. **Product Service** (Port 5002)
   - Manages product catalog and inventory
   - Handles stock checking and reservation
   - Endpoints: `/api/products`, `/api/products/{id}/check-stock`, `/api/products/{id}/reserve`

3. **Order Service** (Port 5003)
   - Processes orders
   - Coordinates with User and Product services
   - Endpoints: `/api/orders`

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (optional, for convenience)

## 🚀 Quick Start

### 1. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:5001/health  # User Service
curl http://localhost:5002/health  # Product Service
curl http://localhost:5003/health  # Order Service
```

### 2. Run Tests

```bash
# Run all unit tests (no services needed)
make test-unit

# Run integration tests (requires services running)
make test-integration

# Run end-to-end tests (requires services running)
make test-e2e

# Run all tests
make test-all
```

## 🧪 Testing Methods Demonstrated

### 1. Unit Testing

**What it tests:** Individual functions and business logic in isolation

**Location:** `{service}/tests/test_unit.py`

**Example:**
```bash
cd user-service
pytest tests/test_unit.py -v
```

**Key Concepts Demonstrated:**
- Testing pure functions (e.g., `calculate_order_total()`)
- Testing API endpoints in isolation
- No external service dependencies
- Fast execution

**Example from presentation:**
```python
def test_calculate_order_total():
    """Test order price calculation (no external calls)"""
    total = calculate_order_total(quantity=2, unit_price=50.00)
    assert total == 100.00
```

### 2. Integration Testing

**What it tests:** Communication between services

**Location:** `tests/test_integration.py`

**Example:**
```bash
# Requires services to be running
make up
pytest tests/test_integration.py -v
```

**Key Concepts Demonstrated:**
- Order Service calling Product Service API
- Order Service calling User Service API
- Verifying correct API contracts
- Testing error handling across services

**Example from presentation:**
```python
def test_order_reserves_inventory_via_api():
    """Order Service should call Product Service to reserve inventory"""
    order_data = {'user_id': 1, 'product_id': 1, 'quantity': 2}
    response = create_order(order_data)
    assert response['status'] == 'RESERVED'
```

### 3. End-to-End (E2E) Testing

**What it tests:** Complete user workflows across all services

**Location:** `tests/test_e2e.py`

**Example:**
```bash
# Requires all services to be running
make up
pytest tests/test_e2e.py -v
```

**Key Concepts Demonstrated:**
- Complete order processing workflow
- User validation → Product check → Inventory reservation → Order creation
- System behavior from client perspective
- Business process validation

**Example from presentation:**
```python
def test_complete_order_workflow():
    """
    Complete workflow:
    1. Client creates order → Order Service
    2. Order Service validates user → User Service
    3. Order Service checks inventory → Product Service
    4. Order Service reserves product → Product Service
    5. Order Service processes payment
    6. Order Service returns result to client
    """
```

### 4. Mocking (Dependency Isolation)

**What it tests:** Service logic without calling real dependencies

**Location:** `order-service/tests/test_unit.py` (see `TestCreateOrderWithMocks`)

**Key Concepts Demonstrated:**
- Using mocks to simulate external service responses
- Testing error handling without real services
- Fast, isolated testing
- Testing service logic independently

**Example:**
```python
@patch('app.requests.get')
def test_create_order_with_mocked_services(mock_get, client):
    """Test order creation without calling real User/Product services"""
    # Mock User Service response
    mock_get.return_value.json.return_value = {'valid': True, 'user': {...}}

    # Test order creation
    response = client.post('/api/orders', json=order_data)
    assert response.status_code == 201
```

## 📚 Testing Strategies from the Presentation

### Challenge 1: Managing Service Dependencies

**Problem:** Services depend on other services to function

**Solutions Demonstrated:**

1. **Mocking Dependencies** (`order-service/tests/test_unit.py`)
   ```python
   @patch('app.requests.get')  # Mock external calls
   def test_with_mocked_dependencies(mock_get, client):
       # Test without real services
   ```

2. **Containerization** (`docker-compose.yml`)
   - All services run in Docker containers
   - Reproducible test environment
   - Easy to start/stop services

### Challenge 2: Test Complexity

**Problem:** Tests become complex with multiple services

**Solutions Demonstrated:**

1. **Test Isolation** - Unit tests don't require services
2. **Clear Test Organization** - Separate unit/integration/e2e tests
3. **Helper Functions** - Wait for service health before testing

### Challenge 3: Continuous Testing

**Problem:** Need to run tests automatically

**Solutions Demonstrated:**

1. **Makefile** - Easy test execution commands
2. **Health Checks** - Services report when ready
3. **Automated Test Suites** - Run all tests with one command

## 🎬 Live Demonstration Guide

### Demo 1: Unit Testing (5 minutes)

Show how unit tests work without services:

```bash
# No services needed!
cd user-service
pytest tests/test_unit.py::TestBusinessLogic -v
```

**Key Points:**
- Fast execution
- No external dependencies
- Tests individual functions
- Easy to debug

### Demo 2: Integration Testing (5 minutes)

Show service-to-service communication:

```bash
# Start services
make up

# Run integration tests
pytest tests/test_integration.py::TestOrderServiceIntegration::test_order_service_calls_user_service_successfully -v
```

**Key Points:**
- Real service communication
- Tests API contracts
- Validates inter-service behavior
- Shows actual HTTP calls

### Demo 3: End-to-End Testing (5 minutes)

Show complete workflow:

```bash
# Services already running
pytest tests/test_e2e.py::TestCompleteOrderWorkflow::test_complete_successful_order_workflow -v
```

**Key Points:**
- Complete business workflow
- All services working together
- Real-world scenario
- Validates entire system

### Demo 4: Mocking (5 minutes)

Show mocking for isolation:

```bash
cd order-service
pytest tests/test_unit.py::TestCreateOrderWithMocks -v
```

**Key Points:**
- No services needed
- Tests error scenarios easily
- Fast execution
- Isolated testing

## 🔍 Service API Examples

### Create an Order (Manual Testing)

```bash
# 1. Check user exists
curl http://localhost:5001/api/users/1

# 2. Check product availability
curl http://localhost:5002/api/products/1

# 3. Create order
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 1, "quantity": 2}'

# 4. Verify order was created
curl http://localhost:5003/api/orders
```

### Test Error Scenarios

```bash
# Invalid user (should fail)
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "product_id": 1, "quantity": 1}'

# Out of stock product (should fail)
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 4, "quantity": 1}'

# Inactive user (should fail)
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3, "product_id": 1, "quantity": 1}'
```

## 📊 Test Coverage

Run tests with coverage:

```bash
# Unit test coverage
cd user-service && pytest tests/test_unit.py --cov=app --cov-report=html
cd product-service && pytest tests/test_unit.py --cov=app --cov-report=html
cd order-service && pytest tests/test_unit.py --cov=app --cov-report=html

# View coverage reports
open htmlcov/index.html
```

## 🛠️ Development

### Running Individual Services

```bash
# User Service
cd user-service
python app.py

# Product Service
cd product-service
python app.py

# Order Service
cd order-service
export USER_SERVICE_URL=http://localhost:5001
export PRODUCT_SERVICE_URL=http://localhost:5002
python app.py
```

### Dev Container

Open this project in VS Code with Dev Containers extension:

1. Open folder in VS Code
2. Click "Reopen in Container"
3. All services will start automatically

## 📝 Test Data

### Initial Users
- User 1: Alice Smith (active)
- User 2: Bob Jones (active)
- User 3: Charlie Brown (inactive)

### Initial Products
- Product 1: Laptop ($999.99, stock: 10)
- Product 2: Mouse ($29.99, stock: 50)
- Product 3: Keyboard ($79.99, stock: 25)
- Product 4: Monitor ($299.99, stock: 0)

## 🎓 Key Learning Points

1. **Unit Tests** - Test individual functions, fast, no dependencies
2. **Integration Tests** - Test service communication, requires services
3. **E2E Tests** - Test complete workflows, validates business processes
4. **Mocking** - Isolate services, test error scenarios, fast feedback
5. **Docker** - Reproducible environment, easy setup
6. **Health Checks** - Ensure services are ready before testing

## 🤝 Mapping to Presentation Concepts

| Presentation Topic | Implementation |
|-------------------|----------------|
| Unit Testing | `{service}/tests/test_unit.py` |
| Integration Testing | `tests/test_integration.py` |
| End-to-End Testing | `tests/test_e2e.py` |
| Contract Testing | Integration tests verify API contracts |
| Mocking | `order-service/tests/test_unit.py` with `@patch` |
| Containerization | `docker-compose.yml`, `Dockerfile` |
| Health Checks | `/health` endpoints |
| Continuous Testing | `Makefile` commands |

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
make clean
make build
make up
```

### Tests failing
```bash
# Ensure services are running
docker-compose ps

# Check service health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Wait a few seconds for services to fully start
sleep 10
```

### Port conflicts
Edit `docker-compose.yml` to use different ports if 5001-5003 are in use.

## 📚 Additional Resources

- [Flask Testing Documentation](https://flask.palletsprojects.com/en/latest/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Microservices Testing Best Practices](https://martinfowler.com/articles/microservice-testing/)

## 📧 Contact

For questions about this demo, refer to the original presentation:
"How are Microservices Tested? Testing Methods, Challenges, and Solutions"

---

**Happy Testing! 🎉**
