# Live Demonstration Script

This script guides you through a live demonstration of microservices testing concepts.

## Preparation (Before Presentation)

```bash
# Clone the repository
git clone <repository-url>
cd MSATestingExample

# Install dependencies
pip install -r requirements.txt

# Build Docker images (do this before the presentation!)
docker-compose build
```

## Demo Flow (25 minutes total)

---

## Part 1: Introduction & Architecture (3 minutes)

**Show:** System architecture diagram in README

**Say:**
- "We have a simple e-commerce system with 3 microservices"
- "User Service manages users, Product Service manages inventory, Order Service coordinates them"
- "Let's see how we test this system using different approaches"

**Terminal:**
```bash
# Show project structure
tree -L 2 -I '__pycache__|*.pyc'
```

---

## Part 2: Unit Testing (5 minutes)

**Say:**
- "Unit tests check individual functions in isolation"
- "They're fast, don't need external services, and test business logic"
- "Let's run unit tests WITHOUT starting any services"

**Terminal:**
```bash
# Show that no services are running
docker-compose ps

# Run unit test for order calculation
cd order-service
pytest tests/test_unit.py::TestBusinessLogic::test_calculate_order_total_basic -v

# Show the test code
cat tests/test_unit.py | grep -A 5 "test_calculate_order_total_basic"
```

**Say:**
- "Notice: This test ran in milliseconds"
- "No network calls, no database, just pure logic"
- "This is perfect for TDD and quick feedback"

**Terminal:**
```bash
# Run all unit tests for one service
pytest tests/test_unit.py -v

# Back to root
cd ..
```

---

## Part 3: Mocking Dependencies (5 minutes)

**Say:**
- "Order Service depends on User and Product services"
- "But we can test it in isolation using mocks"
- "This lets us test error scenarios without complex setups"

**Terminal:**
```bash
# Show the mocking test
cd order-service
cat tests/test_unit.py | grep -A 30 "test_create_order_with_valid_data_returns_201"
```

**Say:**
- "See the @patch decorators? They replace real HTTP calls"
- "We control exactly what the 'external services' return"
- "Let's run it"

**Terminal:**
```bash
pytest tests/test_unit.py::TestCreateOrderWithMocks::test_create_order_with_valid_data_returns_201 -v
```

**Say:**
- "This ran without any real services"
- "But it tested the complete order creation logic"
- "This is how we test error handling easily"

```bash
cd ..
```

---

## Part 4: Starting Services & Integration Testing (7 minutes)

**Say:**
- "Now let's test real service-to-service communication"
- "First, we need to start all services"

**Terminal:**
```bash
# Start all services
docker-compose up -d

# Wait a moment
sleep 5

# Check service health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

**Say:**
- "All services are now running"
- "Integration tests verify that services can actually talk to each other"
- "Let's test Order Service calling Product Service"

**Terminal:**
```bash
# Show integration test
cat tests/test_integration.py | grep -A 20 "test_order_service_calls_product_service_successfully"

# Run it
pytest tests/test_integration.py::TestOrderServiceIntegration::test_order_service_calls_product_service_successfully -v
```

**Say:**
- "This test actually created an order through the API"
- "Order Service called Product Service to reserve inventory"
- "We verified the stock was reduced"
- "This tests the API contract between services"

---

## Part 5: End-to-End Testing (5 minutes)

**Say:**
- "E2E tests validate complete business workflows"
- "They test the system from a user's perspective"
- "Let's test the complete order workflow"

**Terminal:**
```bash
# Show E2E test
cat tests/test_e2e.py | grep -A 10 "test_complete_successful_order_workflow"

# Run it
pytest tests/test_e2e.py::TestCompleteOrderWorkflow::test_complete_successful_order_workflow -v -s
```

**Say:**
- "This test executed the complete workflow:"
- "1. Validated user exists"
- "2. Checked product availability"
- "3. Created order (which calls User Service and Product Service)"
- "4. Verified inventory was updated"
- "5. Confirmed order was stored"
- "This is what the user experiences"

---

## Part 6: Manual Testing & Error Scenarios (3 minutes)

**Say:**
- "Let's manually test some error scenarios"
- "This shows how our services handle failures"

**Terminal:**
```bash
# Successful order
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 2, "quantity": 2}' | jq

# Check the order was created
curl http://localhost:5003/api/orders | jq

# Try with invalid user
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "product_id": 1, "quantity": 1}' | jq

# Try with out-of-stock product
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 4, "quantity": 1}' | jq
```

**Say:**
- "Notice how the system properly handles errors"
- "Invalid user? Rejected with clear error message"
- "Out of stock? Rejected before any changes"
- "This is what integration and E2E tests verify"

---

## Part 7: Summary & Wrap-up (2 minutes)

**Say:**
- "We've demonstrated 4 testing approaches:"
- "1. Unit Tests - Fast, isolated, test business logic"
- "2. Mocking - Test without dependencies, great for error scenarios"
- "3. Integration Tests - Verify service communication"
- "4. E2E Tests - Validate complete workflows"

**Terminal:**
```bash
# Show test summary
echo "=== Test Summary ==="
echo "Unit Tests: Fast, no dependencies"
echo "Integration Tests: Real service calls"
echo "E2E Tests: Complete workflows"
echo ""
echo "All tests: make test-all"
```

**Say:**
- "Each testing approach serves a different purpose"
- "Unit tests give fast feedback during development"
- "Integration tests catch communication issues"
- "E2E tests ensure the business process works"
- "Together, they give confidence in our microservices"

**Terminal:**
```bash
# Cleanup
docker-compose down
```

---

## Quick Commands Reference

```bash
# Start services
make up

# Run all unit tests
make test-unit

# Run integration tests
make test-integration

# Run E2E tests
make test-e2e

# Stop services
make down

# View logs
make logs
```

---

## Troubleshooting During Demo

### Services won't start
```bash
docker-compose down
docker-compose build
docker-compose up -d
sleep 10
```

### Tests are failing
```bash
# Check services are healthy
docker-compose ps
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Restart services
docker-compose restart
sleep 10
```

### Port conflicts
```bash
# Check what's using the ports
lsof -i :5001
lsof -i :5002
lsof -i :5003

# Kill processes or change ports in docker-compose.yml
```

---

## Backup Demonstration (If Docker Issues)

If Docker doesn't work during the demo:

1. **Show the code** - Walk through the test files
2. **Show test output** - Have screenshots/logs prepared
3. **Explain the concepts** - Focus on the testing strategies
4. **Use curl examples** - Show what the APIs look like

---

## Questions You Might Get

**Q: How do you handle test data?**
A: We reset the in-memory database before each test (see `@pytest.fixture(autouse=True)`)

**Q: What about database testing?**
A: This demo uses in-memory data for simplicity, but the same principles apply with real databases

**Q: How do you test asynchronous communication?**
A: This demo focuses on synchronous REST APIs, but message queues would use similar patterns with event waiting

**Q: What about contract testing?**
A: The integration tests verify API contracts - we check request/response formats match expectations

**Q: How long do these tests take?**
A: Unit tests: < 1 second, Integration tests: ~10 seconds, E2E tests: ~30 seconds

---

Good luck with your presentation! 🎉
